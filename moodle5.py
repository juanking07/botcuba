import re
import json
import uuid
import requests
import user_agent
import requests_toolbelt as rt
from functools import partial

HEADERS = {
    'User-Agent': user_agent.generate_user_agent()
}
default_server = json.loads(open("config.json").read())


def login(**kwargs):
    args = {
        "url": default_server["server"]["url"],
        "user": default_server["user"],
        "pwd": default_server["pwd"],
        "scheme": default_server["server"]["scheme"]
    }
    args = kw2args(kwargs, args)
    s = requests.Session()
    s.headers.update(HEADERS)
    token = s.get(f"{args['scheme']}://{args['url']}/login/index.php")
    token = re.findall(
        '<input type="hidden" name="logintoken"' +
        ' value="([^"]*)">', token.text
    )[0]
    s.post(
        f"{args['scheme']}://" +
        f"{args['url']}/login/index.php",
        data={
            'username': args["user"],
            'password': args["pwd"],
            'logintoken': token,
            'anchor': ''
        }
    )
    return s


def getRequiredData(**kwargs):
    args = {
        "url": default_server["server"]["url"],
        "scheme": default_server["server"]["scheme"],
        "session": None,
        "use_image": default_server["server"]["use_image"]
    }

    args = kw2args(kwargs, args)
    web = args["session"].get(
        f"{args['scheme']}://{args['url']}/user/files.php"
    )

    if args["use_image"]:
        web = args["session"].get(
            f"{args['scheme']}://{args['url']}/user/edit.php"
        )

    web = web.text
    sesskey = re.findall('"sesskey":"([^"]*)"', web)[0]
    itemid = re.findall('itemid=([^&amp;]*)', web)[0]
    userid = re.findall('userid="([0-9]*)"', web)[0]
    ctx_id = re.findall('ctx_id=([^&amp;]*)', web)[0]
    client_id = re.findall('"client_id":"([^"]*)"', web)[0]

    return dict(
        sesskey=sesskey,
        itemid=itemid,
        userid=userid,
        ctx_id=ctx_id,
        client_id=client_id
    )


def kw2args(kw, args):
    for i in [*kw.keys()]:
        if i in [*args.keys()]:
            args[i] = kw[i]
    return args


def default(*args, **kwargs):
    return


def upload(**kwargs):
    args = {
        "server_url": default_server["server"]["url"],
        "session": None,
        "file": None,
        "rdata": {},
        "percent_callback": default,
        "scheme": default_server["server"]["scheme"],
        "use_image": default_server["server"]["use_image"],
        "repo_id": str(default_server["server"]["repo_id"])
    }

    upld_url = f"{args['scheme']}://" + \
        f"{args['server_url']}/" + \
        "repository/repository_ajax.php?" + \
        "action=upload"
    b = uuid.uuid4().hex
    args = kw2args(kwargs, args)
    rdata_d = getRequiredData(
        use_image=args["use_image"],
        session=args["session"],
        url=args["server_url"]
    )
    rdata_d.update(args['rdata'])
    fp = open(args['file'], "rb")

    mt = None
    if args["use_image"]:
        args["file"] = args["file"] + ".jpg"
        mt = "image/jpeg"

    args['session'].headers.update({"Host": args["server_url"]})
    tosend = \
        {
            **rdata_d,
            "repo_id": args["repo_id"],
            "title": "",
            "author": "Livan Puig",
            "license": "allrightsreserved",
            "item_id": rdata_d["itemid"],
            "savepath": "/"
        }

    encoder = rt.MultipartEncoder(
        {
            "repo_upload_file": (args["file"], fp, mt),
            **tosend
        }, boundary=b
    )
    callback = partial(args["percent_callback"], encoder=encoder)
    monitor = rt.MultipartEncoderMonitor(encoder, callback)

    r = args["session"].post(
        upld_url,
        data=monitor,
        headers={
            "Content-Type": "multipart/form-data; boundary="+b
        }
    )
    url = json.loads(r.content)
    return url


def delete(**kwargs):
    args = {
        "sesskey": "",
        "client_id": "",
        "filepath": "/",
        "item_id": 1234,
        "filename": "file.temp",
        "username": default_server["user"],
        "password": default_server["pwd"],
        "serverurl": default_server["server"]["url"],
        "scheme": "https",
        "session": None
    }

    draft_url =\
        f"{args['scheme']}://" + \
        f"{args['serverurl']}/" + \
        "repository/draftfiles_ajax.php?" + \
        "action=delete"
    args = kw2args(kwargs, args)

    if args["session"] is None:
        args["session"] = login(
            url=args["serverurl"],
            user=args["username"],
            pwd=args["password"]
        )

    required_data = getRequiredData(
        session=args["session"],
        server_url=args["serverurl"]
    )
    args.update(required_data)
    pargs = {
        "sesskey": args['sesskey'],
        "client_id": args["client_id"],
        "filepath": args["filepath"],
        "itemid": args["item_id"],
        "filename": args["filename"]
    }
    return args["session"].post(draft_url, data=pargs).json()


def list(**kwargs):
    args = {
        "sesskey": "",
        "client_id": "",
        "itemid": "",
        "session": None,
        "scheme": default_server["server"]["scheme"],
        "serverurl": default_server["server"]["url"]
    }

    draft_url =\
        f"{args['scheme']}://" + \
        f"{args['serverurl']}/" + \
        "repository/draftfiles_ajax.php?" + \
        "action=list"
    args = kw2args(kwargs, args)

    ndargs = args.copy()
    del(ndargs["session"])
    return args["session"].post(draft_url, data={
        "filepath": "/", **ndargs
    }).json()


def parse_uploaded_url(url):
    # Example {url}/draftfile.php/172825/user/draft/1234/file.py
    data = re.search("draftfile\.php/([0-9]*)/user/draft/([0-9]*)/([^ ]*)", url)
    if data:
        data = data.span()
        return re.findall(
            "draftfile.php/" +
            "([0-9]*)/user/draft/([0-9]*)/([^ ]*)",
            url[data[0]:data[1]]
        )[0]
    else:
        raise Exception("Invalid url")

# sess = login()
# url  = upload(session = sess, file = "/root/Git/me/serv.py")
# print(url)
# fdata = parse_uploaded_url(url["url"])
# print(delete(session = sess, item_id = fdata[1], filename = fdata[2]))
# print(list(session = sess, **getRequiredData(session = sess)), url["url"])
