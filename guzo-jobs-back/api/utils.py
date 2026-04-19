import base64
import binascii
import html
import re
from decimal import Decimal
from urllib.request import Request, urlopen


def create_notification(recipient, actor, contract, notification_type, title, message):
    from .models import Notification

    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        contract=contract,
        type=notification_type,
        title=title,
        message=message,
    )


def is_same_user(candidate_id, current_id):
    return str(candidate_id) == str(current_id)


def validate_product_image(product_image):
    if not product_image:
        return None

    match = re.match(r'^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$', product_image, re.DOTALL)
    if not match:
        raise Exception('Product image must be a base64 data URL such as data:image/png;base64,...')

    mime_type = match.group(1).lower()
    encoded_payload = match.group(2)

    allowed_mime_types = {
        'image/png': 'PNG',
        'image/jpeg': 'JPEG',
        'image/jpg': 'JPEG',
        'image/webp': 'WEBP',
        'image/gif': 'GIF',
    }

    if mime_type not in allowed_mime_types:
        raise Exception('Unsupported image type. Use PNG, JPEG, WEBP, or GIF.')

    try:
        raw_bytes = base64.b64decode(encoded_payload, validate=True)
    except (ValueError, binascii.Error):
        raise Exception('Invalid base64 image payload.')

    if len(raw_bytes) > 5 * 1024 * 1024:
        raise Exception('Product image must be 5MB or smaller.')

    suspicious_markers = [b'<script', b'</script', b'<?php', b'javascript:', b'onerror=', b'onload=']
    tail_bytes = raw_bytes[-1024:].lower()
    if any(marker in tail_bytes for marker in suspicious_markers):
        raise Exception('Product image contains suspicious trailing script content.')

    detected_format = None
    if raw_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        detected_format = 'PNG'
    elif raw_bytes.startswith(b'\xff\xd8'):
        detected_format = 'JPEG'
    elif raw_bytes.startswith(b'GIF87a') or raw_bytes.startswith(b'GIF89a'):
        detected_format = 'GIF'
    elif len(raw_bytes) >= 12 and raw_bytes[:4] == b'RIFF' and raw_bytes[8:12] == b'WEBP':
        detected_format = 'WEBP'

    if not detected_format:
        raise Exception('Uploaded file is not a valid image.')

    expected_format = allowed_mime_types[mime_type]
    if detected_format != expected_format:
        raise Exception(f'Image metadata does not match its declared type. Expected {expected_format}, got {detected_format or "unknown"}.')

    width = height = None
    if detected_format == 'PNG':
        width = int.from_bytes(raw_bytes[16:20], byteorder='big')
        height = int.from_bytes(raw_bytes[20:24], byteorder='big')
    elif detected_format == 'GIF':
        width = int.from_bytes(raw_bytes[6:8], byteorder='little')
        height = int.from_bytes(raw_bytes[8:10], byteorder='little')
    elif detected_format == 'JPEG':
        offset = 2
        while offset + 1 < len(raw_bytes):
            if raw_bytes[offset] != 0xFF:
                offset += 1
                continue
            marker = raw_bytes[offset + 1]
            offset += 2
            while marker == 0xFF and offset < len(raw_bytes):
                marker = raw_bytes[offset]
                offset += 1

            if marker in [0xD8, 0xD9]:
                continue

            if offset + 1 >= len(raw_bytes):
                break

            segment_length = int.from_bytes(raw_bytes[offset:offset + 2], byteorder='big')
            if segment_length < 2:
                break

            sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
            if marker in sof_markers and offset + 7 < len(raw_bytes):
                height = int.from_bytes(raw_bytes[offset + 3:offset + 5], byteorder='big')
                width = int.from_bytes(raw_bytes[offset + 5:offset + 7], byteorder='big')
                break

            offset += segment_length
    elif detected_format == 'WEBP':
        chunk_type = raw_bytes[12:16]
        if chunk_type == b'VP8X' and len(raw_bytes) >= 30:
            width = 1 + int.from_bytes(raw_bytes[24:27], byteorder='little')
            height = 1 + int.from_bytes(raw_bytes[27:30], byteorder='little')
        elif chunk_type == b'VP8 ' and len(raw_bytes) >= 30:
            width = int.from_bytes(raw_bytes[26:28], byteorder='little') & 0x3FFF
            height = int.from_bytes(raw_bytes[28:30], byteorder='little') & 0x3FFF
        elif chunk_type == b'VP8L' and len(raw_bytes) >= 25:
            packed = int.from_bytes(raw_bytes[21:25], byteorder='little')
            width = 1 + (packed & 0x3FFF)
            height = 1 + ((packed >> 14) & 0x3FFF)

    if not width or not height:
        raise Exception('Product image metadata could not be read.')

    if width < 1 or height < 1:
        raise Exception('Product image dimensions are invalid.')

    if width * height > 25_000_000:
        raise Exception('Product image resolution is too large.')

    if detected_format == 'PNG':
        end_marker = b'\x00\x00\x00\x00IEND\xaeB`\x82'
        end_index = raw_bytes.rfind(end_marker)
        if end_index == -1:
            raise Exception('PNG image is missing a valid end marker.')
        if raw_bytes[end_index + len(end_marker):].strip(b'\x00\r\n\t ') != b'':
            raise Exception('PNG image contains trailing script data.')

    elif detected_format == 'JPEG':
        end_index = raw_bytes.rfind(b'\xff\xd9')
        if end_index == -1:
            raise Exception('JPEG image is missing its end marker.')
        if raw_bytes[end_index + 2:].strip(b'\x00\r\n\t ') != b'':
            raise Exception('JPEG image contains trailing script data.')

    elif detected_format == 'GIF':
        end_index = raw_bytes.rfind(b'\x3b')
        if end_index == -1:
            raise Exception('GIF image is missing its trailer.')
        if raw_bytes[end_index + 1:].strip(b'\x00\r\n\t ') != b'':
            raise Exception('GIF image contains trailing script data.')

    elif detected_format == 'WEBP':
        if len(raw_bytes) < 12 or raw_bytes[:4] != b'RIFF' or raw_bytes[8:12] != b'WEBP':
            raise Exception('WEBP image is malformed.')
        declared_size = int.from_bytes(raw_bytes[4:8], byteorder='little') + 8
        if len(raw_bytes) != declared_size:
            raise Exception('WEBP image contains trailing data or an invalid length header.')

    return product_image


def can_delete_job_post(contract_queryset):
    return not contract_queryset.filter(status__in=['ACCEPTED', 'COMPLETED_BY_ACCEPTOR', 'COMPLETED_BY_POSTER', 'COMPLETED']).exists()


def normalize_name(value):
    return re.sub(r'[^a-z0-9]', '', (value or '').lower())


def digits_only(value):
    return ''.join(ch for ch in str(value or '') if ch.isdigit())


def parse_telebirr_receipt_text(receipt_text):
    compact = re.sub(r'\s+', ' ', html.unescape(receipt_text or '')).strip()

    tx_ref_match = re.search(r'\bDDJ[A-Z0-9]{6,}\b', compact)
    tx_ref = tx_ref_match.group(0) if tx_ref_match else None

    credited_name_match = re.search(r'Credited Party name\s*(.+?)\s*Credited party account', compact, re.IGNORECASE)
    credited_name = credited_name_match.group(1).strip() if credited_name_match else None

    credited_account_match = re.search(r'Credited party account no\s*([0-9*]+)', compact, re.IGNORECASE)
    credited_account = credited_account_match.group(1).strip() if credited_account_match else None

    status_match = re.search(r'transaction status\s*([A-Za-z]+)', compact, re.IGNORECASE)
    transaction_status = status_match.group(1).strip().upper() if status_match else None

    payment_date_match = re.search(r'(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})', compact)
    payment_date = payment_date_match.group(1) if payment_date_match else None

    amount = None
    settled_match = re.search(r'Settled Amount\s*([A-Z0-9]+)?\s*(\d{1,8}(?:\.\d{1,2})?)\s*Birr', compact, re.IGNORECASE)
    if settled_match:
        amount = Decimal(settled_match.group(2))
    else:
        birr_amounts = re.findall(r'(\d{1,8}(?:\.\d{1,2})?)\s*Birr', compact, re.IGNORECASE)
        if birr_amounts:
            amount = Decimal(birr_amounts[0])

    return {
        'tx_ref': tx_ref,
        'credited_name': credited_name,
        'credited_account': credited_account,
        'transaction_status': transaction_status,
        'payment_date': payment_date,
        'amount': amount,
        'raw_excerpt': compact[:1200],
    }


def verify_telebirr_receipt_details(receipt_url, expected_amount, receiver_name, receiver_phone):
    if not receipt_url:
        raise Exception('A telebirr receipt URL is required.')

    if not receipt_url.startswith('https://transactioninfo.ethiotelecom.et/receipt/'):
        raise Exception('Receipt URL must come from transactioninfo.ethiotelecom.et/receipt/.')

    request = Request(receipt_url, headers={'User-Agent': 'travelNotes/1.0'})
    with urlopen(request, timeout=15) as response:
        payload = response.read()

    decoded_text = payload.decode('utf-8', errors='ignore')
    parsed = parse_telebirr_receipt_text(decoded_text)

    if parsed['transaction_status'] != 'COMPLETED':
        raise Exception('Receipt status is not completed.')

    if parsed['amount'] is None:
        raise Exception('Could not read settled amount from receipt.')

    if Decimal(parsed['amount']) < Decimal(expected_amount):
        raise Exception('Settled amount is lower than required escrow amount.')

    if receiver_name:
        expected = normalize_name(receiver_name)
        actual = normalize_name(parsed.get('credited_name'))
        if expected and actual and expected not in actual:
            raise Exception('Credited party name does not match platform receiver name.')

    if receiver_phone:
        expected_digits = digits_only(receiver_phone)
        actual_digits = digits_only(parsed.get('credited_account'))
        if expected_digits and actual_digits:
            if not actual_digits.endswith(expected_digits[-4:]):
                raise Exception('Credited telebirr account does not match configured receiver account.')

    if not parsed.get('tx_ref'):
        raise Exception('Could not read transaction reference from receipt.')

    return parsed