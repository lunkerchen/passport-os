"""Optional browser check: uv run --with playwright python tests/test_portrait_mode_browser.py."""
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
html=(root/'main/apps/home/phone_setup.html').read_text()
original=bytearray(14280);original[:8]=b'PC38\x04\0\0\0'
for i in range(1,256):original[8+i*4+3]=255
original[12:16]=bytes((0,0,255,255));original[1032:]=bytes([1])*13248
stored=bytearray(original)
errors=[]

def route_request(route):
    global stored
    request=route.request;path=urlsplit(request.url).path
    if path=='/':return route.fulfill(status=200,content_type='text/html',body=html)
    if path=='/api/avatar':
        if request.method=='POST':
            stored=bytearray(request.post_data_buffer)
            return route.fulfill(status=200,json={'ok':True})
        return route.fulfill(status=200,content_type='application/octet-stream',body=bytes(stored))
    if path=='/api/profile':data={'name':'模式測試','signature':'','address':'','city':'','lat':'','lon':'','region':'','radio_city':'','country_code':'','avatar':True,'share_image':False}
    elif path=='/api/setup':data={'state':'idle','saved_network':True,'saved_networks':['Test Network']}
    elif path=='/api/cities':data=[['test','臺北',25.03,121.56,'臺灣','臺北','TW']]
    elif path=='/api/cards':data={'max':6,'per_image_bytes':24576,'storage_free':1900000,'storage_reserve':65536,'images':[]}
    elif path=='/api/muse':data={'token_set':False,'paired':False,'proxy_host':'','proxy_port':0}
    elif path=='/api/networks':data=[{'ssid':'Test Network','secure':True}]
    else:data={'ok':True}
    route.fulfill(status=200,json=data)

with sync_playwright() as playwright:
    chrome=Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    browser=playwright.chromium.launch(headless=True,**({'executable_path':str(chrome)} if chrome.exists() else {}))
    try:
        page=browser.new_page(viewport={'width':375,'height':850})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/*',route_request)
        page.add_init_script('window.__T=42')
        def open_profile():
            page.goto('http://passport.test/')
            page.locator('#keepSaved').wait_for(state='visible')
            page.locator('#keepSaved').click()
            page.locator('#portraitSection > summary').click()
            page.locator('#portraitPresetFlat').wait_for(state='visible')
        open_profile()
        assert page.locator('#portraitPresetColor').is_checked()
        assert not page.locator('#photoTools').is_visible()
        page.locator('#portraitPresetFlat').check()
        assert stored[5]==0,'preview must not write immediately'
        page.locator('#save').click();page.locator('#step3').wait_for(state='visible')
        assert stored[5]==1 and stored[8:]==original[8:]
        open_profile()
        assert page.locator('#portraitPresetFlat').is_checked()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'mobile overflow'
        output=root/'.cache/portrait-mode-mobile.png';output.parent.mkdir(exist_ok=True)
        page.locator('#portraitSection').screenshot(path=str(output))
        page.locator('#portraitPresetColor').check()
        page.locator('#save').click();page.locator('#step3').wait_for(state='visible')
        assert stored==original
        stored=bytearray(4976);stored[:8]=b'PT35\x03\0\0\0'
        open_profile()
        assert page.locator('#portraitPresetFlat').is_checked()
        assert page.locator('#portraitPresetColor').is_disabled()
        assert not errors,errors
        print('Browser phone flow: color -> monochrome -> reload -> color without selecting a file, original RGB retained, legacy guidance and mobile layout PASS')
    finally:browser.close()
