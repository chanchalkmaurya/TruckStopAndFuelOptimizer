from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from fuel.models import FuelStation
from fuel.tasks import geocode_station


@receiver(pre_save, sender=FuelStation)
def fuel_station_pre_save(
    sender,
    instance,
    **kwargs
):

    if not instance.pk:

        instance._should_geocode = True
        return

    try:

        old = FuelStation.objects.get(
            pk=instance.pk
        )

        instance._should_geocode = (
            old.address != instance.address
            or old.city != instance.city
            or old.state != instance.state
        )

    except FuelStation.DoesNotExist:

        instance._should_geocode = True
        
        
@receiver(post_save, sender=FuelStation)
def fuel_station_post_save(
    sender,
    instance,
    created,
    **kwargs
):

    if getattr(
        instance,
        "_should_geocode",
        False
    ):
        geocode_station(instance.id)