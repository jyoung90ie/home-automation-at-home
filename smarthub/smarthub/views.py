class UUIDView:
    """Changes Django DB lookup field to use UUID field"""

    slug_field = "uuid"
    slug_url_kwarg = "uuid"
