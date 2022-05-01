# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.pluginHandler import cPluginHandler
from resources.lib.util import cUtil
import re

SITE_IDENTIFIER = 'moviesever_com'
SITE_NAME = 'MoviesEver'
SITE_ICON = 'moviesever.png'

URL_MAIN = 'http://moviesever.com/'

SERIESEVER_IDENTIFIER = 'seriesever_net'


def load():
    oParams = ParameterHandler()

    oGui = cGui()
    oGui.addFolder(cGuiElement('Neue Filme', SITE_IDENTIFIER, 'showNewMovies'), oParams)
    oGui.addFolder(cGuiElement('Kategorien', SITE_IDENTIFIER, 'showGenresMenu'), oParams)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'), oParams)
    oGui.setEndOfDirectory()


def __isSeriesEverAvaiable():
    cph = cPluginHandler()

    return any(
        site['id'] == SERIESEVER_IDENTIFIER
        for site in cph.getAvailablePlugins()
    )


def __getHtmlContent(sUrl=None):
    oParams = ParameterHandler()
    # Test if a url is available and set it
    if sUrl is None and not oParams.exist('sUrl'):
        logger.error("There is no url we can request.")
        return False
    else:
        if sUrl is None:
            sUrl = oParams.getValue('sUrl')
    # Make the request
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    oRequest.addHeaderEntry('Accept', '*/*')

    return oRequest.request()


def showNewMovies():
    oGui = cGui()

    showMovies(oGui, URL_MAIN, False)

    oGui.setView('movies')
    oGui.setEndOfDirectory()


def showSearch():
    logger.info('load showSearch')
    oGui = cGui()

    sSearchText = oGui.showKeyBoard()
    if sSearchText not in [False, '']:
        _search(oGui, sSearchText)
    else:
        return

    oGui.setView('movies')
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    showMovies(oGui, f'{URL_MAIN}?s={sSearchText}', True)


def showGenresMenu():
    logger.info('load showGenresMenu')
    oParams = ParameterHandler()
    sPattern = '<li class="cat-item.*?href="(.*?)"\s*?>(.*?)<'

    # request
    sHtmlContent = __getHtmlContent(URL_MAIN)
    # parse content
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sPattern)

    oGui = cGui()

    if aResult[0]:
        for link, title in aResult[1]:
            guiElement = cGuiElement(title, SITE_IDENTIFIER, 'showMovies')
            #guiElement.setMediaType('fGenre') # not necessary
            oParams.addParams({'sUrl': link, 'bShowAllPages': True})
            oGui.addFolder(guiElement, oParams)

    oGui.setEndOfDirectory()


def showMovies(oGui = False, sUrl=False, bShowAllPages=False):
    logger.info('load showMovies')
    oParams = ParameterHandler()

    if not sUrl:
        sUrl = oParams.getValue('sUrl')

    if oParams.exist('bShowAllPages'):
        bShowAllPages = oParams.getValue('bShowAllPages')

    sPagePattern = f'{sUrl}page/(.*?)/'

    # request
    sHtmlContent = __getHtmlContent(sUrl)
    # parse content
    oParser = cParser()
    aPages = oParser.parse(sHtmlContent, sPagePattern)

    pages = aPages[1][-1] if aPages[0] and bShowAllPages else 1
    bInternGui = False

    if not oGui:
        bInternGui = True
        oGui = cGui()

    sHtmlContentPage = __getHtmlContent(sUrl)
    __getMovies(oGui, sHtmlContentPage)

    if int(pages) > 1:
        for x in range(2, int(pages) + 1):
            sHtmlContentPage = __getHtmlContent(f'{sUrl}page/{str(x)}/')
            __getMovies(oGui, sHtmlContentPage)

    if bInternGui:
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def __getMovies(oGui, sHtmlContent):
    oParams = ParameterHandler()
    sBlockPattern = '<div class="moviefilm">.*?href="(.*?)"(.*?)src="(.*?)".*?alt="(.*?)"'

    # parse content
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sBlockPattern)
    unescape = cUtil().unescape
    if aResult[0]:
        for link, span, img, title in aResult[1]:
            title = unescape(title.decode('utf-8')).encode('utf-8')
            # TODO: Looking for span isn't the best way, but the only difference I found
            if "span" in span:
                guiElement = cGuiElement(title, SITE_IDENTIFIER, 'showHosters')
                guiElement.setMediaType('movie')
                guiElement.setThumbnail(img)
                oParams.addParams({'sUrl': link, 'Title': title})
                oGui.addFolder(guiElement, oParams, bIsFolder=False)

            elif __isSeriesEverAvaiable():
                if url := __getSELink(link):
                    guiElement = cGuiElement(title, SERIESEVER_IDENTIFIER, 'showMovie')
                    guiElement.setMediaType('movie')
                    guiElement.setThumbnail(img)
                    oParams.addParams({'sUrl': url})
                    oGui.addFolder(guiElement, oParams)


def __decode(text):
    text = text.replace('&#8211;', '-')
    text = text.replace('&#038;', '&')
    text = text.replace('&#8217;', '\'')
    return text


def __getSELink(sUrl):
    sPattern = '<a href="(http://seriesever.com/serien/.*?)" target="MoviesEver">'

    # request
    sHtmlContent = __getHtmlContent(sUrl)
    # parse content
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sPattern)

    if aResult[0]:
        return aResult[1][0]

    return False


def showHosters():
    logger.info('load showHosters')
    oParams = ParameterHandler()
    sPattern = 'a href="(' + oParams.getValue('sUrl') + '.*?/)"'

    # request
    sHtmlContent = __getHtmlContent()
    # parse content
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sPattern)

    hosters = []

    hosters = getHoster(sHtmlContent, hosters)

    if aResult[0]:
        for link in aResult[1]:
            sHtmlContentTmp = __getHtmlContent(link)
            hosters = getHoster(sHtmlContentTmp, hosters)

    if hosters:
        hosters.append('getHosterUrl')

    return hosters


def getHoster(sHtmlContent, hosters):
    sPattern = '<p><iframe src="(.*?)"'

    # parse content
    oParser = cParser()

    aResult = oParser.parse(sHtmlContent, sPattern)

    if aResult[0]:
        hoster = {'link': aResult[1][0]}

        hname = 'Unknown Hoster'
        try:
            hname = re.compile('^(?:https?:\/\/)?(?:[^@\n]+@)?([^:\/\n]+)', flags=re.I | re.M).findall(hoster['link'])[0]
        except:
            pass

        hoster['name'] = hname
        hoster['displayedName'] = hname

        hosters.append(hoster)

    return hosters


def getHosterUrl(sUrl=False):
    oParams = ParameterHandler()

    logger.info(oParams.getAllParameters())

    if not sUrl:
        sUrl = oParams.getValue('url')

    result = {'streamUrl': sUrl, 'resolved': False}
    return [result]
