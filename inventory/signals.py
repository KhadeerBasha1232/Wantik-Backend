from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RemovalRequest, RemovalRequestItem, Product
from django.db import transaction

@receiver(post_save, sender=RemovalRequest)
def update_stock_on_approval(sender, instance, **kwargs):
    """
    Deduct stock from Product's stock_count and quantity_added when all statuses are approved.
    Only deduct if stock_deducted is False to prevent duplicates.
    """
    print(f"Signal triggered for RemovalRequest {instance.request_no}")
    if (
        instance.accounts_status == "approved"
        and instance.gm_status == "approved"
        and instance.mgmt_status == "approved"
        and not instance.stock_deducted
    ):
        print(f"All statuses approved for RemovalRequest {instance.request_no}, deducting stock")
        try:
            with transaction.atomic():
                for item in instance.items.select_related('product').all():
                    product = item.product
                    if product.stock_count >= item.quantity and product.quantity_added >= item.quantity:
                        print(
                            f"Deducting {item.quantity} from {product.product_name} "
                            f"(current stock_count: {product.stock_count}, quantity_added: {product.quantity_added})"
                        )
                        product.stock_count -= item.quantity
                        product.quantity_added -= item.quantity
                        product.save()
                    else:
                        error_message = (
                            f"Insufficient values for {product.product_name}: "
                            f"Requested {item.quantity}, "
                            f"Available stock_count: {product.stock_count}, "
                            f"Available quantity_added: {product.quantity_added}"
                        )
                        print(error_message)
                        raise ValueError(error_message)
                instance.stock_deducted = True
                instance.save()
                print(f"Stock deducted and stock_deducted set to True for RemovalRequest {instance.request_no}")
        except Exception as e:
            print(f"Error deducting stock for RemovalRequest {instance.request_no}: {str(e)}")
            raise
    else:
        print(
            f"Conditions not met for stock deduction: "
            f"accounts_status={instance.accounts_status}, "
            f"gm_status={instance.gm_status}, "
            f"mgmt_status={instance.mgmt_status}, "
            f"stock_deducted={instance.stock_deducted}"
        )
