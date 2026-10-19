import graphene


class EscrowRecipientType(graphene.ObjectType):
    provider = graphene.String()
    name = graphene.String()
    account_number = graphene.String()
    updated_at = graphene.DateTime()


class UserType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    email = graphene.String()
    phone_number = graphene.String()
    profile_picture = graphene.String()
    bio = graphene.String()
    fayda_linked = graphene.Boolean()

    def resolve_email(self, info):
        user = info.context.user
        return self.email if user.is_authenticated and (user.pk == self.pk or user.is_staff) else None

    def resolve_phone_number(self, info):
        user = info.context.user
        return self.phone_number if user.is_authenticated and (user.pk == self.pk or user.is_staff) else None

    def resolve_fayda_linked(self, info):
        return hasattr(self, 'fayda_identity')


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
        user = info.context.user
        return self.escrow_payments.all() if user.is_authenticated and (user.pk in (self.poster_id, self.acceptor_id) or user.is_staff) else []


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
        user = info.context.user
        if not user.is_authenticated:
            return []
        return [contract for contract in self.contract.all() if user.pk in (contract.poster_id, contract.acceptor_id) or user.is_staff]
