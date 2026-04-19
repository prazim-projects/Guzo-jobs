import graphene


class UserType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    email = graphene.String()
    phone_number = graphene.String()
    profile_picture = graphene.String()
    bio = graphene.String()


class EscrowPaymentType(graphene.ObjectType):
    id = graphene.ID()
    amount = graphene.Float()
    payment_method = graphene.String()
    tx_ref = graphene.String()
    receipt_url = graphene.String()
    verification_note = graphene.String()
    verified_at = graphene.DateTime()
    status = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()


class TransactionSummaryType(graphene.ObjectType):
    total_paid = graphene.Float()
    total_received = graphene.Float()
    total_transacted = graphene.Float()

class ContractType(graphene.ObjectType):
    id = graphene.ID()
    job_post = graphene.Field(lambda: JobPostingType)
    poster = graphene.Field(UserType)
    acceptor = graphene.Field(UserType)
    status = graphene.String()
    agreed_price = graphene.Float()
    preferred_payment_method = graphene.String()
    preferred_chapa_bank = graphene.String()
    escrow_payments = graphene.List(EscrowPaymentType)
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()

    def resolve_job_post(self, info):
        return self.job_post

    def resolve_poster(self, info):
        return self.poster

    def resolve_acceptor(self, info):
        return self.acceptor

    def resolve_escrow_payments(self, info):
        return self.escrow_payments.all()


class ComplaintType(graphene.ObjectType):
    id = graphene.ID()
    contract = graphene.Field(ContractType)
    filed_by = graphene.Field(UserType)
    against = graphene.Field(UserType)
    reason = graphene.String()
    status = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()


class SupportTicketType(graphene.ObjectType):
    id = graphene.ID()
    user = graphene.Field(UserType)
    contract = graphene.Field(ContractType)
    subject = graphene.String()
    message = graphene.String()
    status = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()


class NotificationType(graphene.ObjectType):
    id = graphene.ID()
    recipient = graphene.Field(UserType)
    actor = graphene.Field(UserType)
    contract = graphene.Field(ContractType)
    type = graphene.String()
    title = graphene.String()
    message = graphene.String()
    is_read = graphene.Boolean()
    created_at = graphene.DateTime()

class JobPostingType(graphene.ObjectType):
    id = graphene.ID()
    title = graphene.String()
    description = graphene.String()
    user = graphene.Field(UserType)
    expires_at = graphene.DateTime()
    origin = graphene.String()
    destination = graphene.String()
    product_image = graphene.String()
    post_type = graphene.String()
    contracts = graphene.List(ContractType)
    price = graphene.Float()

    def resolve_user(self, info):
        return self.user

    def resolve_contracts(self, info):
        return self.contract.all()
