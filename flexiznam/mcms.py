import re
import pandas as pd
from requests.exceptions import InvalidURL
from flexiznam.config import PARAMETERS, get_password
from pymcms.main import McmsSession

def get_mouse_info(mouse_name, username, password=None):
    """Load mouse info from mcms in a dataframe

    Args:
        mouse_name (str): Mouse name
        username (str): Mcms username
        password (str, optional): Mcms password. Defaults to None.

    Returns:
        dict: Mouse info
    """
    if password is None:
        password = get_password(username=username, app="mcms")
    mcms_sess = McmsSession(username=username, password=password)
    try:
        original_data = mcms_sess.get_animal(name=mouse_name)
    except InvalidURL:
        raise InvalidURL(f"Mouse {mouse_name} not found under your PPL")

    # convert to camel case for flexlilims
    mouse_data = {}
    pattern = re.compile(r"(?<!^)(?=[A-Z])")
    for k, v in original_data.items():
        if k == "id":  # id is a reserved word in flexilims
            mouse_data["mcms_id"] = v
        elif k == "name":
            mouse_data["animal_name"] = v
        else:
            mouse_data[pattern.sub("_", k).lower()] = v

    if not mouse_name:
        raise IOError("Failed to download mouse info")
    return mouse_data


def get_procedures(mouse_name, username, password=None):
    """Load mouse procedures from mcms in a dataframe

    Args:
        mouse_name (str): Mouse name
        username (str): Mcms username
        password (str, optional): Mcms password. Defaults to None.

    Returns:
        dict: Mouse procedures
    """
    if password is None:
        password = get_password(username=username, app="mcms")
    mcms_sess = McmsSession(username=username, password=password)
    procedures = mcms_sess.get_procedures(mouse_name)
    out = []
    for proc in procedures:
        proc_dict = {}
        for k, v in proc.items():
            if k == "animal":
                assert v["name"] == mouse_name
            elif k == "protocol":
                if v is not None:
                    proc_dict["protocol_code"] = v["protocolCode"]
                    proc_dict["project_licence"] = v["projectLicenceNumber"]
            elif k == "procedure":
                proc_dict["procedure_name"] = v["name"]
            else:
                proc_dict[k] = v
        out.append(proc_dict)
    return pd.DataFrame(out)
