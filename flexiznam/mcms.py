import re
import pandas as pd
from pymcms.main import McmsSession
from flexiznam.config import PARAMETERS, get_password


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
    original_data = mcms_sess.get_animal(name=mouse_name)
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
        if proc["procedure"]["name"] == "Administration of substances into the brain under recovery anaesthesia":
            break
        proc_dict = {}
        animal = proc.pop("animal")
        assert animal["name"] == mouse_name
        proc_dict["start_date"] = proc.pop("startDate")
        prot = proc.pop("protocol")
        if prot:
            proc_dict["project_licence"] = prot.pop("projectLicence")
            proc_dict["protocol_code"] = prot.pop("protocolCode")
        proc = proc.pop("procedure")
        proc_dict["procedure_name"] = proc["name"]
        proc_dict["description"] = proc["description"]
        out.append(proc_dict)
    return pd.DataFrame(out)
