"""
Lightsail networking construct (Static IP).

Uses L1 constructs for Lightsail resources.
"""

from constructs import Construct
from aws_cdk import aws_lightsail as lightsail

from utils.config_loader import NesterConfig


class LightsailNetworking(Construct):
    """
    Creates Lightsail networking resources:
    - Static IP attached to the instance

    Note: Firewall rules are configured on the instance directly.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: NesterConfig,
        instance_name: str,
    ) -> None:
        super().__init__(scope, id)

        self.config = config
        prefix = config.resource_prefix

        # Create Static IP if enabled
        self.static_ip = None

        if config.lightsail.static_ip.enabled:
            # Create Static IP and attach to instance via attached_to property
            self.static_ip = lightsail.CfnStaticIp(
                self,
                "StaticIp",
                static_ip_name=f"{prefix}-static-ip",
                attached_to=instance_name,  # Attach directly to instance
            )

    @property
    def ip_address(self) -> str | None:
        """Get the static IP address (available after deployment)."""
        if self.static_ip:
            return self.static_ip.attr_ip_address
        return None