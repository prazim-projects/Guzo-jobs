import graphql_jwt
import graphene
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from graphql_jwt.shortcuts import create_refresh_token, get_token

from .types import (
    UserType,
    JobPostingType,
    ContractType,
    EscrowPaymentType,
    ComplaintType,
    SupportTicketType,
    NotificationType,
)
from .models import *
from .utils import (
    create_notification,
    validate_product_image,
    is_same_user,
    can_delete_job_post,
    verify_telebirr_receipt_details,
)


class editProfile(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        email = graphene.String(required=False)
        phone_number = graphene.String(required=False)
        bio = graphene.String(required=False)
        profile_picture = graphene.String(required=False)

    @classmethod
    def mutate(cls, root, info, email=None, phone_number=None, bio=None, profile_picture=None):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to edit your profile.")

        if email is not None:
            user.email = email
        if phone_number is not None:
            user.phone_number = phone_number
        if bio is not None:
            user.bio = bio
        if profile_picture is not None:
            user.profile_picture = profile_picture

        user.save()
        return editProfile(user=user)
    

class RegisterUser(graphene.Mutation):
    user = graphene.Field(UserType)
    token = graphene.String()
    refresh_token = graphene.String()

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        phone_number = graphene.String(required=True)

    @classmethod
    def mutate(cls, root, info, username, password, phone_number):
        User = get_user_model()
        user = User(username=username, phone_number=phone_number)
        user.set_password(password)
        user.save()
        token = get_token(user)
        refresh_token = create_refresh_token(user)

        return RegisterUser(user=user, token=token, refresh_token=refresh_token)

class createJobPost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=True)
        expires_at = graphene.DateTime(required=True)
        origin = graphene.String(required=True)
        destination = graphene.String(required=True)
        product_image = graphene.String(required=False)
        post_type = graphene.String(required=True)
        price = graphene.Int(required=True)

    jobPost = graphene.Field(JobPostingType)

    @classmethod
    def mutate(cls, root, info, title, description, expires_at, origin, destination, post_type, price, product_image=None):
        # print(f"DEBUG: Auth Header -> {info.context.META.get('HTTP_AUTHORIZATION')}")
        # print(f"DEBUG: User in Context -> {info.context.user}")
        price = int(price) 
        user = info.context.user
        if user.is_anonymous:
            raise Exception("you must be logged in to create a job post.")

        if (price < 0):
            raise Exception("Money can't be less than 0 birr")

        product_image = validate_product_image(product_image)

        jobPost = JobPosting(
            title=title,
            description=description,
            expires_at=expires_at,
            user=user,
            origin=origin,
            destination=destination,
            product_image=product_image,
            post_type=post_type,
            price=price
        )
        jobPost.save()
        return createJobPost(jobPost=jobPost)
    

class acceptJobPost(graphene.Mutation):
    class Arguments:
        job_post_id = graphene.ID(required=True) 
        status = graphene.String(required=False)
        preferred_payment_method = graphene.String(required=False)
        preferred_chapa_bank = graphene.String(required=False)

    contract = graphene.Field(lambda: ContractType)

    @classmethod
    def mutate(cls, root, info, job_post_id, status=None, preferred_payment_method=None, preferred_chapa_bank=None):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to Interact with job post.")
       
        try:
            job_post = JobPosting.objects.get(pk=job_post_id)
        except JobPosting.DoesNotExist:
            raise Exception("Job post not found.")

        if is_same_user(job_post.user_id, user.id):
            raise Exception("You cannot accept your own job post")

        existing_application = Contract.objects.filter(
            job_post=job_post, 
            acceptor=user, 
            status__in=[Contract.Status.PENDING, Contract.Status.ACCEPTED]
        ).first()
        
        if existing_application:
            raise Exception("You have already applied for this job.")

        preferred_method = (preferred_payment_method or Contract.PreferredPaymentMethod.TELEBIRR).upper()
        if preferred_method != Contract.PreferredPaymentMethod.TELEBIRR:
            raise Exception('Only TELEBIRR is supported for payment preference.')

        normalized_bank = None

        contract = Contract(
            job_post=job_post,
            poster=job_post.user,
            acceptor=user,
            status=status if status else Contract.Status.PENDING,
            agreed_price=job_post.price if job_post.price else 0.0,
            preferred_payment_method=preferred_method,
            preferred_chapa_bank=normalized_bank,
        )
        contract.save()

        create_notification(
            recipient=job_post.user,
            actor=user,
            contract=contract,
            notification_type=Notification.Type.JOB_ACCEPTED,
            title='New job application',
            message=f'{user.username} applied to your job "{job_post.title}".',
        )
        return acceptJobPost(contract=contract)
    

class ConfirmJobAcceptance(graphene.Mutation):
    class Arguments:
        contract_id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    @classmethod
    def mutate(cls, root, info, contract_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to confirm job acceptance.")

        try:
            contract = Contract.objects.get(pk=contract_id)
        except Contract.DoesNotExist:
            raise Exception("Contract not found.")

        if not is_same_user(contract.poster_id, user.id):
            raise Exception("Only the job owner can confirm acceptance.")

        if contract.status != Contract.Status.PENDING:
            raise Exception("This contract is not in pending status.")

        # Accept this contract
        contract.status = Contract.Status.ACCEPTED
        contract.save()

        # Reject all other pending contracts for this job
        Contract.objects.filter(
            job_post=contract.job_post,
            status=Contract.Status.PENDING
        ).exclude(pk=contract_id).update(status=Contract.Status.CANCELLED)

        create_notification(
            recipient=contract.acceptor,
            actor=contract.poster,
            contract=contract,
            notification_type=Notification.Type.JOB_ACCEPTED,
            title='Application accepted',
            message=f'Your application for "{contract.job_post.title}" was accepted. Await escrow deposit.',
        )

        return ConfirmJobAcceptance(success=True)


class InitiateEscrowPayment(graphene.Mutation):
    class Arguments:
        contract_id = graphene.ID(required=True)
        receipt_url = graphene.String(required=True)

    payment = graphene.Field(EscrowPaymentType)
    verified = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, contract_id, receipt_url):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to fund escrow.')

        try:
            contract = Contract.objects.get(pk=contract_id)
        except Contract.DoesNotExist:
            raise Exception('Contract not found.')

        if not is_same_user(contract.poster_id, user.id):
            raise Exception('Only the job poster can fund escrow.')

        if contract.status != Contract.Status.ACCEPTED:
            raise Exception('Escrow can only be funded after acceptance.')

        if EscrowPayment.objects.filter(contract=contract, status=EscrowPayment.Status.PAID).exists():
            raise Exception('Escrow is already funded for this contract.')

        telebirr_receiver_name = getattr(settings, 'TELEBIRR_RECEIVER_NAME', '')
        telebirr_receiver_phone = getattr(settings, 'TELEBIRR_RECEIVER_PHONE', '')
        missing = []
        if not telebirr_receiver_name:
            missing.append('TELEBIRR_RECEIVER_NAME')
        if not telebirr_receiver_phone:
            missing.append('TELEBIRR_RECEIVER_PHONE')
        if missing:
            raise Exception(f'Telebirr receiver configuration missing: {", ".join(missing)}')

        payment = EscrowPayment.objects.create(
            contract=contract,
            payer=user,
            amount=contract.agreed_price,
            payment_method=EscrowPayment.Method.TELEBIRR,
            tx_ref='PENDING_VERIFICATION',
            receipt_url=receipt_url,
            status=EscrowPayment.Status.INITIATED,
            verification_note='Receipt submitted. Pending verification.',
        )

        try:
            parsed = verify_telebirr_receipt_details(
                receipt_url=receipt_url,
                expected_amount=contract.agreed_price,
                receiver_name=telebirr_receiver_name,
                receiver_phone=telebirr_receiver_phone,
            )
            payment.tx_ref = parsed['tx_ref']
            payment.status = EscrowPayment.Status.PAID
            payment.verified_at = timezone.now()
            payment.verification_note = (
                f"Verified telebirr receipt ({parsed.get('payment_date') or 'unknown date'}) "
                f"for settled amount {parsed.get('amount')} Birr."
            )
            payment.save(update_fields=['tx_ref', 'status', 'verified_at', 'verification_note', 'updated_at'])
        except Exception as verification_error:
            payment.verification_note = f'Verification failed: {verification_error}'
            payment.save(update_fields=['verification_note', 'updated_at'])
            return InitiateEscrowPayment(
                payment=payment,
                verified=False,
                message=str(verification_error),
            )

        create_notification(
            recipient=contract.acceptor,
            actor=user,
            contract=contract,
            notification_type=Notification.Type.ESCROW_PAID,
            title='Escrow funded',
            message=f'Escrow has been funded via TELEBIRR for "{contract.job_post.title}". You can now start work.',
        )

        return InitiateEscrowPayment(
            payment=payment,
            verified=True,
            message='Telebirr receipt verified and escrow marked as paid.',
        )

class RejectJobApplication(graphene.Mutation):
    class Arguments:
        contract_id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    @classmethod
    def mutate(cls, root, info, contract_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to reject job application.")

        try:
            contract = Contract.objects.get(pk=contract_id)
        except Contract.DoesNotExist:
            raise Exception("Contract not found.")

        if contract.status != Contract.Status.PENDING:
            raise Exception("This contract is not in pending status.")

        # Delete contract to make job available again
        contract.delete()

        return RejectJobApplication(success=True)

class confirmJobCompleted(graphene.Mutation):
    class Arguments:
        contract_id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    @classmethod
    def mutate(cls, root, info, contract_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to confirm job completion.")

        try:
            contract = Contract.objects.get(pk=contract_id)
        except Contract.DoesNotExist:
            raise Exception("Contract not found.")

        # Check if user is either the acceptor or the poster
        if not is_same_user(contract.acceptor_id, user.id) and not is_same_user(contract.poster_id, user.id):
            raise Exception("Only contract parties can confirm completion.")

        paid_escrow = EscrowPayment.objects.filter(
            contract=contract,
            status=EscrowPayment.Status.PAID,
        ).first()

        if not paid_escrow:
            raise Exception('Escrow must be paid by the job poster before completion can be confirmed.')

        # Handle different completion scenarios
        if contract.status == Contract.Status.ACCEPTED:
            # Either party can initiate completion
            if is_same_user(contract.acceptor_id, user.id):
                contract.status = Contract.Status.COMPLETED_BY_ACCEPTOR
            elif is_same_user(contract.poster_id, user.id):
                contract.status = Contract.Status.COMPLETED_BY_POSTER
            contract.save()
            return confirmJobCompleted(success=True)
            
        elif contract.status == Contract.Status.COMPLETED_BY_ACCEPTOR:
            # Only poster can confirm acceptor's completion
            if not is_same_user(contract.poster_id, user.id):
                raise Exception("Only the job poster can confirm completion initiated by the acceptor.")
            contract.status = Contract.Status.COMPLETED
            contract.save()
            paid_escrow.status = EscrowPayment.Status.RELEASED
            paid_escrow.save(update_fields=['status', 'updated_at'])
            create_notification(
                recipient=contract.acceptor,
                actor=contract.poster,
                contract=contract,
                notification_type=Notification.Type.JOB_COMPLETED,
                title='Escrow released',
                message=f'Job "{contract.job_post.title}" marked complete. Escrow has been released.',
            )
            return confirmJobCompleted(success=True)
            
        elif contract.status == Contract.Status.COMPLETED_BY_POSTER:
            # Only acceptor can confirm poster's completion
            if not is_same_user(contract.acceptor_id, user.id):
                raise Exception("Only the job acceptor can confirm completion initiated by the poster.")
            contract.status = Contract.Status.COMPLETED
            contract.save()
            paid_escrow.status = EscrowPayment.Status.RELEASED
            paid_escrow.save(update_fields=['status', 'updated_at'])
            create_notification(
                recipient=contract.poster,
                actor=contract.acceptor,
                contract=contract,
                notification_type=Notification.Type.JOB_COMPLETED,
                title='Escrow released',
                message=f'Job "{contract.job_post.title}" marked complete. Escrow has been released.',
            )
            return confirmJobCompleted(success=True)
            
        else:
            raise Exception("Contract is not in a state that allows completion confirmation.")


class CreateComplaint(graphene.Mutation):
    class Arguments:
        contract_id = graphene.ID(required=True)
        reason = graphene.String(required=True)
        against_user_id = graphene.ID(required=False)

    complaint = graphene.Field(ComplaintType)

    @classmethod
    def mutate(cls, root, info, contract_id, reason, against_user_id=None):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to file a complaint.')

        try:
            contract = Contract.objects.get(pk=contract_id)
        except Contract.DoesNotExist:
            raise Exception('Contract not found.')

        if not is_same_user(contract.acceptor_id, user.id) and not is_same_user(contract.poster_id, user.id):
            raise Exception('Only contract participants can file complaints.')

        against = None
        if against_user_id:
            try:
                against = UserProfile.objects.get(pk=against_user_id)
            except UserProfile.DoesNotExist:
                raise Exception('Target user not found.')

        complaint = Complaint.objects.create(
            contract=contract,
            filed_by=user,
            against=against,
            reason=reason,
        )

        other_party = contract.poster if user == contract.acceptor else contract.acceptor
        create_notification(
            recipient=other_party,
            actor=user,
            contract=contract,
            notification_type=Notification.Type.COMPLAINT_OPENED,
            title='Complaint opened',
            message=f'A complaint has been opened on "{contract.job_post.title}".',
        )

        return CreateComplaint(complaint=complaint)


class CreateSupportTicket(graphene.Mutation):
    class Arguments:
        subject = graphene.String(required=True)
        message = graphene.String(required=True)
        contract_id = graphene.ID(required=False)

    ticket = graphene.Field(SupportTicketType)

    @classmethod
    def mutate(cls, root, info, subject, message, contract_id=None):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to contact support.')

        contract = None
        if contract_id:
            try:
                contract = Contract.objects.get(pk=contract_id)
            except Contract.DoesNotExist:
                raise Exception('Contract not found.')

            if str(contract.poster_id) != str(user.id) and str(contract.acceptor_id) != str(user.id):
                raise Exception('You can only open support for your own jobs/contracts.')

            if SupportTicket.objects.filter(contract=contract).exists():
                raise Exception('A support ticket already exists for this job contract.')

        ticket = SupportTicket.objects.create(user=user, contract=contract, subject=subject, message=message)
        return CreateSupportTicket(ticket=ticket)


class DeleteJobPost(graphene.Mutation):
    class Arguments:
        job_post_id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, job_post_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to delete a job post.')

        try:
            job_post = JobPosting.objects.prefetch_related('contract').get(pk=job_post_id)
        except JobPosting.DoesNotExist:
            raise Exception('Job post not found.')

        if not is_same_user(job_post.user_id, user.id):
            raise Exception('Only the job owner can delete this job post.')

        contracts = job_post.contract.all()
        if not can_delete_job_post(contracts):
            raise Exception('This job cannot be deleted because it already has an active contract.')

        contracts.filter(status=Contract.Status.PENDING).delete()
        job_post.delete()
        return DeleteJobPost(success=True)


class MarkNotificationRead(graphene.Mutation):
    class Arguments:
        notification_id = graphene.ID(required=True)

    notification = graphene.Field(NotificationType)

    @classmethod
    def mutate(cls, root, info, notification_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to update notifications.')

        try:
            notification = Notification.objects.get(pk=notification_id, recipient=user)
        except Notification.DoesNotExist:
            raise Exception('Notification not found.')

        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return MarkNotificationRead(notification=notification)
    
class ObtainJSONWebToken(graphql_jwt.JSONWebTokenMutation):
    user = graphene.Field(UserType)

    @classmethod
    def resolve(cls, root, info, **kwargs):
        return cls(user=info.context.user)

class Mutation(graphene.ObjectType):
    token_auth = ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

    RegisterUser = RegisterUser.Field()
    createJobPost = createJobPost.Field()
    editProfile = editProfile.Field()
    acceptJobPost = acceptJobPost.Field()
    confirmJobContract = ConfirmJobAcceptance.Field()
    initiateEscrowPayment = InitiateEscrowPayment.Field()
    rejectJobApplication = RejectJobApplication.Field()
    confirmJobCompleted = confirmJobCompleted.Field()
    createComplaint = CreateComplaint.Field()
    createSupportTicket = CreateSupportTicket.Field()
    deleteJobPost = DeleteJobPost.Field()
    markNotificationRead = MarkNotificationRead.Field()