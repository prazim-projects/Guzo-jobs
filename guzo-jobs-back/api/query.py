import graphene
from django.db.models import Sum
from django.db.models import Q

from .models import UserProfile, JobPosting, Notification, Complaint, SupportTicket, EscrowPayment
from .types import UserType, JobPostingType, NotificationType, ComplaintType, SupportTicketType, TransactionSummaryType

class Query(graphene.ObjectType):
    allUsers = graphene.List(UserType)
    user_by_id = graphene.Field(UserType, id=graphene.ID(required=True))
    allJobs = graphene.Field(graphene.List(lambda: JobPostingType))
    availableJobs = graphene.Field(graphene.List(lambda: JobPostingType))
    jobs_by_contract_status = graphene.Field(graphene.List(lambda: JobPostingType), status=graphene.String(required=True))
    my_notifications = graphene.List(NotificationType)
    my_complaints = graphene.List(ComplaintType)
    my_support_tickets = graphene.List(SupportTicketType)
    my_transaction_summary = graphene.Field(TransactionSummaryType)
    my_jobs = graphene.List(JobPostingType)

    def resolve_allUsers(root, info):
        return UserProfile.objects.all()
    
    def resolve_user_by_id(root, info, id):
        try:
            return UserProfile.objects.get(pk=id)
        except UserProfile.DoesNotExist:
            return None
        
    def resolve_allJobs(root, info):
        return JobPosting.objects.select_related('user').prefetch_related('contract').all()
    
    def resolve_availableJobs(root, info):
        return JobPosting.objects.select_related('user').prefetch_related('contract').exclude(contract__status__in=[ 'ACCEPTED', 'COMPLETED' ]).distinct()

    def resolve_jobs_by_contract_status(root, info, status):
        return JobPosting.objects.filter(contract__status=status).select_related('user').prefetch_related('contract').distinct()

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

    def resolve_my_jobs(root, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in.')

        return JobPosting.objects.select_related('user').prefetch_related(
            'contract__acceptor',
            'contract__poster',
            'contract__escrow_payments',
        ).filter(
            Q(user=user) | Q(contract__acceptor=user) | Q(contract__poster=user)
        ).distinct()
    