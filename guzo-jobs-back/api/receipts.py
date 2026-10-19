"""Bounded, origin-restricted receipt retrieval and fail-closed verification."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from html.parser import HTMLParser
from io import BytesIO
import ipaddress
import json
import re
import socket
from http.client import HTTPSConnection
from urllib.request import HTTPSHandler
import unicodedata
from urllib.error import URLError, HTTPError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from zoneinfo import ZoneInfo

from django.utils import timezone

MAX_RECEIPT_BYTES = 2 * 1024 * 1024
HOSTS = {'CBE': 'mbreciept.cbe.com.et', 'TELEBIRR': 'transactioninfo.ethiotelecom.et'}


class ReceiptError(ValueError):
    pass


@dataclass(frozen=True)
class Receipt:
    provider: str
    reference: str
    recipient_name: str
    recipient_account: str
    amount: Decimal
    paid_at: datetime
    status: str
    digest: str = ''


def normalize_name(value):
    return ' '.join(unicodedata.normalize('NFKC', value or '').casefold().split())


def normalize_account(value, provider):
    value = re.sub(r'[\s+()-]', '', value or '')
    if provider == 'TELEBIRR' and value.startswith('0'):
        value = '251' + value[1:]
    return value


def account_matches(actual, expected, provider):
    actual, expected = normalize_account(actual, provider), normalize_account(expected, provider)
    if not re.fullmatch(r'\d{9,16}', expected):
        return False
    if '*' not in actual:
        return actual == expected
    # Providers compress the hidden portion (CBE's four stars do not mean four digits).
    if not re.fullmatch(r'\d+\*+\d{4,}', actual):
        return False
    prefix, suffix = re.split(r'\*+', actual)
    return len(prefix) + len(suffix) >= 5 and len(expected) > len(prefix) + len(suffix) and expected.startswith(prefix) and expected.endswith(suffix)


def receipt_url(value):
    if not isinstance(value, str) or len(value) > 500 or any(ord(c) < 33 for c in value):
        raise ReceiptError('Paste a valid CBE or Telebirr receipt link.')
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        raise ReceiptError('Invalid receipt address.')
    if parts.scheme != 'https' or parts.username or parts.password or port not in (None, 443) or parts.query or parts.fragment:
        raise ReceiptError('Receipt links must use HTTPS with no extra parameters.')
    provider = next((key for key, host in HOSTS.items() if parts.hostname == host), None)
    pattern = r'/v2-[A-Za-z0-9_-]{8,120}/?' if provider == 'CBE' else r'/receipt/[A-Z0-9]{6,40}/?'
    if not provider or not re.fullmatch(pattern, parts.path):
        raise ReceiptError('Use the original CBE or Telebirr receipt link.')
    return provider, urlunsplit(('https', HOSTS[provider], parts.path.rstrip('/'), '', ''))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ReceiptError('The receipt redirected to another address. Use its original receipt link.')


class PinnedHTTPSHandler(HTTPSHandler):
    def __init__(self, addresses):
        super().__init__()
        self.addresses = addresses

    def https_open(self, request):
        addresses = self.addresses

        class Connection(HTTPSConnection):
            def connect(self):
                # Use validated addresses while verifying TLS against the original hostname.
                def connect_address(_address, timeout, source_address=None):
                    for family, socktype, proto, _, address in addresses:
                        connection = socket.socket(family, socktype, proto)
                        connection.settimeout(timeout)
                        try:
                            connection.connect(address)
                            return connection
                        except OSError:
                            connection.close()
                    raise OSError('Receipt provider connection failed.')
                self._create_connection = connect_address
                super().connect()

        return self.do_open(Connection, request, context=self._context)


def fetch_receipt(url):
    provider, canonical = receipt_url(url)
    host = 'mb.cbe.com.et' if provider == 'CBE' else HOSTS[provider]
    endpoint = 'https://mb.cbe.com.et/api/v1/transactions/public/transaction-detail/' + canonical.rsplit('/', 1)[-1] if provider == 'CBE' else canonical
    headers = {'User-Agent': 'GuzoJobs-ReceiptVerifier/1.0', 'Accept': 'application/json,text/html,application/pdf', 'Accept-Encoding': 'identity'}
    if provider == 'CBE':
        # Public client identifiers published by CBE's receipt viewer (not credentials).
        headers.update({'X-App-ID': 'd1292e42-7400-49de-a2d3-9731caa4c819', 'X-App-Version': '0a01980b-9859-1369-8198-59f403820000'})
    # Exact provider hosts only; prohibit private destinations and inherited proxy settings.
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ReceiptError('Receipt provider address could not be verified.')
        opener = build_opener(ProxyHandler({}), NoRedirect(), PinnedHTTPSHandler(addresses))
        request = Request(endpoint, headers=headers)
        with opener.open(request, timeout=15) as response:
            if response.status != 200:
                raise ReceiptError('The receipt provider did not return a receipt.')
            content_type = response.headers.get_content_type()
            if content_type not in ('application/json', 'text/html', 'application/pdf'):
                raise ReceiptError('The provider returned an unsupported receipt format.')
            payload = response.read(MAX_RECEIPT_BYTES + 1)
            if len(payload) > MAX_RECEIPT_BYTES:
                raise ReceiptError('The receipt exceeds the supported size.')
    except ReceiptError:
        raise
    except (OSError, URLError, HTTPError, ValueError):
        raise ReceiptError('The receipt provider is unavailable. Please try again later.') from None
    return provider, canonical, payload, content_type


class ReceiptHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.rows, self.row, self.cell = [], [], [], None
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if tag == 'tr':
            self.row = []
        if tag in ('td', 'th'):
            if self.cell is not None:
                self.handle_endtag('td')
            self.cell = []

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(' '.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.row:
            self.rows.append(self.row)
            self.row = []
        if tag in ('td', 'th', 'tr', 'p', 'div', 'br'):
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)
            if self.cell is not None:
                self.cell.append(data)


def document_text(payload, content_type):
    if len(payload) > MAX_RECEIPT_BYTES:
        raise ReceiptError('The receipt exceeds the supported size.')
    if content_type == 'application/pdf' or payload.startswith(b'%PDF-'):
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(payload), strict=True)
            if reader.is_encrypted or len(reader.pages) > 3:
                raise ReceiptError('Encrypted or long PDFs require manual review.')
            text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        except ReceiptError:
            raise
        except Exception:
            raise ReceiptError('The provider PDF could not be read. Contact support for review.') from None
        if not text.strip():
            raise ReceiptError('This PDF is an image. Use the online receipt link or contact support for review.')
        return text, []
    parser = ReceiptHTML()
    try:
        parser.feed(payload.decode('utf-8', errors='strict'))
    except (UnicodeError, ValueError):
        raise ReceiptError('The receipt page could not be read.') from None
    return ''.join(parser.parts), parser.rows


def _match(pattern, text, label):
    matches = re.findall(pattern, text, re.I)
    values = {re.sub(r'\s+', ' ', value).strip() for value in matches}
    if len(values) != 1:
        raise ReceiptError(f'Could not uniquely verify the receipt {label}.')
    return values.pop()


def parse_receipt(payload, content_type, provider):
    if len(payload) > MAX_RECEIPT_BYTES:
        raise ReceiptError('The receipt exceeds the supported size.')
    if provider == 'CBE' and content_type == 'application/json':
        try:
            data = json.loads(payload)
            if not isinstance(data, dict) or data.get('creditCurrency') != 'ETB' or data.get('isOtherBank'):
                raise ValueError()
            name, account, reference = data['creditAccountHolder'], data['creditAccountNo'], data['id']
            amount = Decimal(str(data['amountCredited']))
            paid_at = datetime.fromisoformat(data['dateTimes'][0].replace('Z', '+00:00'))
            status = data['status'].upper()
            if data.get('thirdPartyStatus') and data['thirdPartyStatus'].upper() != 'SUCCESS':
                status = 'FAILED'
            if not isinstance(name, str) or not name.strip() or not isinstance(account, str) or not re.fullmatch(r'[0-9*]+', account):
                raise ValueError()
            if not re.fullmatch(r'[A-Z0-9]{6,40}', reference) or not amount.is_finite() or amount <= 0 or amount != amount.quantize(Decimal('.01')) or paid_at.utcoffset() is None:
                raise ValueError()
            return Receipt(provider, reference, name, account, amount, paid_at, status, sha256(payload).hexdigest())
        except (KeyError, TypeError, ValueError, IndexError, AttributeError, InvalidOperation):
            raise ReceiptError('CBE returned incomplete or invalid transaction details.') from None
    text, rows = document_text(payload, content_type)
    compact = ' '.join(text.split())
    if provider == 'CBE':
        name = _match(r'Receiver\s*:\s*(.+?)\s+Account\s*:', compact, 'receiver name')
        account = _match(r'Receiver\s*:.*?\s+Account\s*:\s*([\d*]+)', compact, 'receiver account')
        reference = _match(r'Reference No\.\s*\(VAT Invoice No\)\s*:\s*([A-Z0-9]+)', compact, 'reference')
        amount = _match(r'Transferred Amount\s*:\s*([\d,]+(?:\.\d{1,2})?)\s*ETB', compact, 'transferred amount')
        date = _match(r'Payment Date & Time\s*:\s*(.+?)\s+Reference No', compact, 'payment date')
        status = _match(r'Status\s*:\s*([A-Z]+)', compact, 'status')
        date_format = '%b %d, %Y, %I:%M %p'
    elif provider == 'TELEBIRR':
        # HTML tables preserve field/value boundaries even with bilingual labels.
        fields = {}
        for index, row in enumerate(rows):
            if len(row) == 2:
                key = row[0].split('/')[-1].strip().casefold()
                if key not in ('credited party name', 'credited party account no', 'transaction status'):
                    continue
                if key in fields and fields[key] != row[1]:
                    raise ReceiptError('The receipt contains conflicting fields.')
                fields[key] = row[1]
            if len(row) == 3 and 'invoice no' in row[0].casefold() and index + 1 < len(rows):
                values = rows[index + 1]
                if len(values) == 3:
                    if 'invoice' in fields:
                        raise ReceiptError('The receipt contains multiple invoices.')
                    fields.update({'invoice': values[0], 'date': values[1], 'amount': values[2]})
        if fields.get('credited party name'):
            name = fields.get('credited party name', '')
            account = fields.get('credited party account no', '')
            reference, date = fields.get('invoice', ''), fields.get('date', '')
            amount = _match(r'^([\d,]+(?:\.\d{1,2})?)\s+Birr$', fields.get('amount', ''), 'settled amount')
            status = fields.get('transaction status', '')
        else:
            # Text PDF fallback; never substitute the fee-inclusive total for settled amount.
            name = _match(r'Credited Party name\s+([^\n]+)', text, 'receiver name')
            account = _match(r'Credited party account no\s+([\d*]+)', text, 'receiver account')
            status = _match(r'transaction status\s+([A-Z]+)', text, 'status')
            date = _match(r'(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})', text, 'payment date')
            reference = _match(r'\b([A-Z]{3}[A-Z0-9]{7,20})\b', text, 'invoice')
            amount = _match(r'Settled Amount\s+(?:[A-Z0-9]+\s+)?(?:\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2}\s+)?([\d,]+(?:\.\d{1,2})?)\s+Birr', compact, 'settled amount')
        date_format = '%d-%m-%Y %H:%M:%S'
    else:
        raise ReceiptError('Unsupported receipt provider.')
    try:
        paid_at = datetime.strptime(date, date_format).replace(tzinfo=ZoneInfo('Africa/Addis_Ababa'))
        amount = Decimal(amount.replace(',', ''))
    except (ValueError, InvalidOperation):
        raise ReceiptError('Invalid receipt amount or payment date.') from None
    if not name or not account or not re.fullmatch(r'[A-Z0-9]{6,40}', reference) or amount <= 0:
        raise ReceiptError('Receipt is missing required payment details.')
    return Receipt(provider, reference, name, account, amount, paid_at, status.upper(), sha256(payload).hexdigest())


def verify_receipt(url, recipient, expected_amount, earliest_payment):
    provider, canonical, payload, content_type = fetch_receipt(url)
    if provider != recipient.provider or not recipient.is_active:
        raise ReceiptError('This escrow payment method is not available.')
    receipt = parse_receipt(payload, content_type, provider)
    if provider == 'CBE' and content_type == 'application/json':
        if json.loads(payload).get('encodedReceipt') != canonical:
            raise ReceiptError('The CBE transaction does not match its receipt link.')
    if receipt.status != 'COMPLETED':
        raise ReceiptError('The receipt does not show a completed payment.')
    if normalize_name(receipt.recipient_name) != normalize_name(recipient.name):
        raise ReceiptError('The receipt recipient name does not match the escrow account.')
    if not account_matches(receipt.recipient_account, recipient.account_number, provider):
        raise ReceiptError('The receipt recipient account does not match the escrow account.')
    if receipt.amount != Decimal(expected_amount):
        raise ReceiptError('The transferred amount must exactly match the escrow amount, excluding fees.')
    if receipt.paid_at < earliest_payment - timedelta(minutes=5) or receipt.paid_at > timezone.now() + timedelta(minutes=5):
        raise ReceiptError('The receipt must be for a payment made after this contract was created.')
    if provider == 'TELEBIRR' and canonical.rsplit('/', 1)[-1] != receipt.reference:
        raise ReceiptError('The receipt invoice does not match its link.')
    return receipt, canonical
