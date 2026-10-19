import graphene
from django.db.models import Sum
from django.utils import timezone
from graphql import GraphQLError
from .models import EscrowRecipient
from .types import EscrowRecipientType

def page(queryset, limit=50, offset=0):
    if not 1 <= limit <= 100 or offset < 0 or offset > 10000:
        raise GraphQLError("Use a limit of 1–100 and an offset of 0–10000.")
    return queryset.order_by("-id")[offset:offset + limit]

def jobs():
    return JobPosting.objects.select_related("user", "user__fayda_identity").prefetch_related("contract__poster", "contract__acceptor", "contract__escrow_payments")
from django.db.models import Q

from .models import UserProfile, JobPosting, Notification, Complaint, SupportTicket, EscrowPayment
from .types import UserType, JobPostingType, NotificationType, ComplaintType, SupportTicketType, TransactionSummaryType

class Query(graphene.ObjectType):
    allUsers = graphene.List(UserType)
    user_by_id = graphene.Field(UserType, id=graphene.ID(required=True))
    allJobs = graphene.List(JobPostingType, limit=graphene.Int(default_value=50), offset=graphene.Int(default_value=0))
    availableJobs = graphene.List(JobPostingType, limit=graphene.Int(default_value=50), offset=graphene.Int(default_value=0))
    jobs_by_contract_status = graphene.Field(graphene.List(lambda: JobPostingType), status=graphene.String(required=True))
    my_notifications = graphene.List(NotificationType)
    my_complaints = graphene.List(ComplaintType)
    my_support_tickets = graphene.List(SupportTicketType)
    my_transaction_summary = graphene.Field(TransactionSummaryType)
    my_jobs = graphene.List(JobPostingType, limit=graphene.Int(default_value=50), offset=graphene.Int(default_value=0))
    escrow_recipients = graphene.List(EscrowRecipientType)

    def resolve_escrow_recipients(root, info):
        if not info.context.user.is_authenticated:
            raise GraphQLError("You must be logged in.")
        return EscrowRecipient.objects.filter(is_active=True).order_by("provider")

    def resolve_allUsers(root, info):
        if not info.context.user.is_staff:
            raise GraphQLError("Staff access required.")
        return UserProfile.objects.all()[:100]
    
    def resolve_user_by_id(root, info, id):
        try:
            return UserProfile.objects.get(pk=id)
        except UserProfile.DoesNotExist:
            return None
        
    def resolve_allJobs(root, info, limit=50, offset=0):
        return page(jobs(), limit, offset)
    
    def resolve_availableJobs(root, info, limit=50, offset=0):
        return page(jobs().filter(expires_at__gt=timezone.now()).exclude(contract__status__in=['ACCEPTED', 'COMPLETED', 'COMPLETED_BY_ACCEPTOR', 'COMPLETED_BY_POSTER']).distinct(), limit, offset)

    def resolve_jobs_by_contract_status(root, info, status):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError('You must be logged in.')
        return page(jobs().filter(Q(user=user) | Q(contract__acceptor=user), contract__status=status).distinct())

    def resolve_my_notifications(root, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in.')
        return Notification.objects.filter(recipient=user).select_related('actor', 'contract')

    def resolve_my_complaints(root, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in.')
        return Complaint.objects.filter(filed_by=user).select_related('contract', 'against')

    def resolve_my_support_tickets(root, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in.')
        return SupportTicket.objects.filter(user=user)

    def resolve_my_transaction_summary(root, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in.')

        paid_total = EscrowPayment.objects.filter(
            payer=user,
            status__in=[EscrowPayment.Status.PAID, EscrowPayment.Status.RELEASED],
        ).aggregate(total=Sum('amount')).get('total') or 0

        received_total = EscrowPayment.objects.filter(
            contract__acceptor=user,
            status=EscrowPayment.Status.RELEASED,
        ).aggregate(total=Sum('amount')).get('total') or 0

        return TransactionSummaryType(
            total_paid=float(paid_total),
            total_received=float(received_total),
            total_transacted=float(paid_total) + float(received_total),
        )

    def resolve_my_jobs(root, info, limit=50, offset=0):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in.')

        return page(jobs().filter(Q(user=user) | Q(contract__acceptor=user) | Q(contract__poster=user)).distinct(), limit, offset)
    