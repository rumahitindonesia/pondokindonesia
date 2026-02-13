from core.models import TenantSubscription, PricingPlan
from crm.models import Santri, Donatur

class SubscriptionService:
    @staticmethod
    def get_active_subscription(tenant):
        """
        Returns the active subscription for a tenant.
        """
        if not tenant:
            return None
        
        try:
            sub = tenant.subscription
            if sub.is_valid():
                return sub
        except TenantSubscription.DoesNotExist:
            pass
        return None

    @staticmethod
    def check_feature_access(tenant, feature_name):
        """
        Checks if a tenant has access to a specific feature.
        Features: 'can_use_ai', 'can_use_ipaymu', 'can_use_whatsapp'
        """
        # Superusers or Global context might have different rules, 
        # but here we strictly follow tenant subscription.
        if not tenant:
            return True # Or False depending on security posture (here we assume Global = All access?)
            
        sub = SubscriptionService.get_active_subscription(tenant)
        if not sub or not sub.plan:
            return False
            
        return getattr(sub.plan, feature_name, False)

    @staticmethod
    def check_quota_reached(tenant, model_class):
        """
        Returns True if the tenant has reached their quota for a specific model class.
        Supported model_class: Santri, Donatur
        """
        if not tenant:
            return False
            
        sub = SubscriptionService.get_active_subscription(tenant)
        if not sub or not sub.plan:
            return True # No active subscription means cannot add anything? Or use a default?
            
        current_count = model_class.objects.filter(tenant=tenant).count()
        
        limit = 0
        if model_class == Santri:
            limit = sub.plan.max_santri
        elif model_class == Donatur:
            limit = sub.plan.max_donatur
            
        if limit == 0: # 0 means unlimited
            return False
            
        return current_count >= limit
