import requests
import xml.etree.ElementTree as ET
import datetime
import logging

logging.basicConfig(level=logging.INFO)


SERVER = "your-server" # e.g. https://your-server/api/3.21/sites/site-id/workbooks/workbook-id
SITE_NAME = "octopus"
TABLEAU_REST_API_VERSION = "3.18"
XMLNS = {"t": "http://tableau.com/api"}


def _check_status(server_response, success_code):
    """
    Checks the server response for possible errors.
    'server_response'       the response received from the server
    'success_code'          the expected success code for the response
    Throws an RequestException if the API call fails.

    https://github.com/tableau/rest-api-samples/blob/4960b097e2bd2beb17cb34d96a7918fd2cadadc4/python/publish_workbook.py#L97
    """
    if server_response.status_code != success_code:
        parsed_response = ET.fromstring(server_response.text)

        # Obtain the 3 xml tags from the response: error, summary, and detail tags
        error_element = parsed_response.find("t:error", namespaces=XMLNS)
        summary_element = parsed_response.find(".//t:summary", namespaces=XMLNS)
        detail_element = parsed_response.find(".//t:detail", namespaces=XMLNS)

        # Retrieve the error code, summary, and detail if the response contains them
        code = (
            error_element.get("code", "unknown")
            if error_element is not None
            else "unknown code"
        )
        summary = (
            summary_element.text if summary_element is not None else "unknown summary"
        )
        detail = detail_element.text if detail_element is not None else "unknown detail"
        error_message = "{0}: {1} - {2}".format(code, summary, detail)
        raise requests.exceptions.RequestException(error_message)
    return


def _sign_in(token_name, token_secret, site_name, server):
    """
    Returns the authentication token and the site ID used in subsequent calls to the server.

    Typically, an authentication token is valid for 240 minutes. With administrator permissions on Tableau Server,
    you can change this timeout. More info on credential tokens here:
    https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_authentication.htm#sign_in
    """

    # Builds the request
    xml_request = ET.Element("tsRequest")
    credentials_element = ET.SubElement(
        xml_request,
        "credentials",
        personalAccessTokenName=token_name,
        personalAccessTokenSecret=token_secret,
    )
    ET.SubElement(credentials_element, "site", contentUrl=site_name)
    xml_request = ET.tostring(xml_request)

    # Sign in
    url = f"{server}/api/{TABLEAU_REST_API_VERSION}/auth/signin"
    data = xml_request
    headers = {"Content-Type": "application/xml"}
    response = requests.post(url, data, headers)
    _check_status(response, 200)

    server_response = response.text.encode("ascii", errors="backslashreplace").decode(
        "utf-8"
    )

    # Reads and parses the response
    parsed_response = ET.fromstring(server_response)

    # Gets the auth token and site ID needed for further
    auth_token = parsed_response.find("t:credentials", namespaces=XMLNS).get("token")
    site_id = parsed_response.find(".//t:site", namespaces=XMLNS).get("id")
    return auth_token, site_id



def refresh_workbook(
    token_name, token_secret, workbook_name, workbook_id, site_name=SITE_NAME, server=SERVER
):
    """Refreshes a workbook given a workbook id and authentication token."""

    auth_token, site_id = _sign_in(token_name, token_secret, site_name, server)
    error_message = f"There was a problem refreshing the workbook '{workbook_name}' with ID {workbook_id}."

    # Creates empty request data
    xml_request = ET.Element("tsRequest")
    xml_request = ET.tostring(xml_request)

    # Refresh job
    url = f"{server}/api/{TABLEAU_REST_API_VERSION}/sites/{site_id}/workbooks/{workbook_id}/refresh"
    data = xml_request
    headers = {"X-Tableau-Auth": auth_token, "Content-Type": "application/xml"}
    try:
        response = requests.post(url, data, headers=headers)
        _check_status(response, 202)
        logging.info(
            f"The data of workbook '{workbook_name}' with id {workbook_id} was refreshed at {datetime.datetime.now()}."
        )
        return
    except requests.exceptions.RequestException as re:
        if str(re).startswith("409093: Resource Conflict"):
            logging.warning(re)
            pass
        else:
            logging.info(error_message)
            raise re
    except Exception as e:
        logging.info(error_message)
        raise e


def _get_wbs_to_refresh(site_id, auth_token, tag, server=SERVER):
    """Collects workbooks with given tag."""

    url = f"{server}/api/{TABLEAU_REST_API_VERSION}/sites/{site_id}/workbooks?filter=tags:eq:{tag}"
    headers = {"Content-Type": "application/json", "X-Tableau-Auth": auth_token, "Accept": "application/json"}
    response = requests.get(url, headers=headers)
    _check_status(response, 200)
    if int(response.json()['pagination']['totalAvailable']) > 0:
        wbs_to_refresh = [(wb["name"], wb["id"]) for wb in response.json()["workbooks"]["workbook"]]
    else:
        logging.info(f"No workbooks found with tag {tag}")
        return None
    return wbs_to_refresh

def refresh_tagged_wbs(token_name, token_secret, tag, site_name=SITE_NAME, server=SERVER):
    """Bulk refresh of workbooks given a list of workbooks [(name, id), ...]"""

    auth_token, site_id = _sign_in(token_name, token_secret, site_name, server)
    wbs_to_refresh = _get_wbs_to_refresh(site_id, auth_token, tag)
    if wbs_to_refresh:
        for wb_name, wb_id in wbs_to_refresh:
            refresh_workbook(
                token_name=token_name,
                token_secret=token_secret,
                workbook_name=wb_name,
                workbook_id=wb_id
            )
