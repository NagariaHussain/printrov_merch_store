import frappe
import razorpay
from frappe.integrations.utils import (
    make_get_request,
    make_post_request,
)

# constants
BASE_URL = "https://api.printrove.com/"
SECONDS_IN_YEAR = 364 * 24 * 60 * 60


def get_printrove_access_token():
    token = frappe.cache.get_value("printrove_access_token")
    if token:
        return token

    printrove_settings = frappe.get_cached_doc("Printrove Settings")
    auth_route = "api/external/token"
    response = make_post_request(
        f"{BASE_URL}{auth_route}",
        data={
            "email": printrove_settings.email,
            "password": printrove_settings.get_password("password"),
        },
    )

    access_token = response["access_token"]

    # store for a year
    frappe.cache.set_value(
        "printrove_access_token",
        access_token,
        expires_in_sec=SECONDS_IN_YEAR,
    )

    return access_token


def make_printrove_request(
    endpoint, method="GET", data=None, params=None
):
    access_token = get_printrove_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    make_request = (
        make_get_request if method == "GET" else make_post_request
    )
    response = make_request(
        f"{BASE_URL}{endpoint}",
        headers=headers,
        data=data,
        params=params,
    )
    return response


@frappe.whitelist(allow_guest=True)
def get_available_couriers(
    pincode: str,
    country: str = "India",
    weight_in_gms: int = 800,
    cod: bool = False,
):
    serviceability_endpoint = "api/external/serviceability"
    params = {
        "pincode": pincode,
        "country": country,
        "weight": weight_in_gms,
        "cod": "true" if cod else "false",
    }

    response = make_printrove_request(
        serviceability_endpoint, params=params
    )
    couriers = response.get("couriers", [])

    return couriers


def get_razorpay_client():
    razorpay_settings = frappe.get_cached_doc(
        "Printrove Razorpay Settings"
    )
    key_id = razorpay_settings.key_id
    key_secret = razorpay_settings.get_password("key_secret")

    return razorpay.Client(auth=(key_id, key_secret))