from aiohttp import ClientSession, FormData
from aiofiles import open
from io import BytesIO

async def upload(session: ClientSession, fp: str = None, io: BytesIO = None):
    data = FormData()
    
    if fp:
        async with open(fp, "rb") as file:
            io = await file.read()
    
    fname = "video.mp4"
    if fp: fname = fp.rsplit("/", 1)[-1]
    print(fname)
    data.add_field('fileToUpload', io, filename=fname)
    for key, value in {'reqtype': 'fileupload', 'userhash': ''}.items():
        data.add_field(key, str(value))
                    
    response = await session.post("https://catbox.moe/user/api.php", data=data) 
    url = await response.text()
    return url