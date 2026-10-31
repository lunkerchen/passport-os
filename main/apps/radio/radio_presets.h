#pragma once
#include "radio_player.h"

// User-selected Taipei catalog stays fixed instead of being replaced by city search.
inline constexpr bool kRadioFixedCatalog = true;

inline constexpr RadioStation kRadioPresets[] = {
#ifdef PASSPORT_RADIO_HLS_TEST
    {"经济之声", "HLS测试 · TS/AAC", "http://ngcdn002.cnr.cn/live/jjzs/index.m3u8", 0},
    {"华语金曲", "HLS测试 · AAC分片", "http://ls.qingting.fm/live/3412131.m3u8?bitrate=64", 0},
    {"凤凰资讯", "HLS测试 · TS/AAC", "http://playtv-live.ifeng.com/live/06OLEEWQKN4_audio.m3u8", 0},
    {"SomaFM", "美国 · MP3测试", "https://ice6.somafm.com/groovesalad-128-mp3", 0},
    {"MANGORADIO", "德国 · MP3测试", "https://mangoradio.stream.laut.fm/mangoradio", 0},
    {"中国之声", "MP3回归测试", "http://lhttp.qingting.fm/live/15318317/64k.mp3", 0},
#else
    {"ICRT", "臺北・英語與音樂", "https://stream.rcs.revma.com/x27mfpztxp3vv", 0},
    {"中廣新聞網", "臺北・新聞時事", "https://stream.rcs.revma.com/78fm9wyy2tzuv", 0},
    {"中廣流行網", "臺北・生活綜合", "https://stream.rcs.revma.com/aw9uqyxy2tzuv", 0},
    {"中廣音樂網", "臺北・音樂節目", "https://stream.rcs.revma.com/ndk05tyy2tzuv", 0},
    {"九八新聞台", "臺北・新聞訪談", "https://stream.rcs.revma.com/pntx1639ntzuv", 0},
    {"飛碟電台", "臺北・談話與音樂", "https://stream.rcs.revma.com/em90w4aeewzuv", 0},
    {"臺北健康電臺", "臺北・健康生活", "http://fm901.cityfm.tw:8080/901.mp3", 0},
    {"臺北廣播電臺", "臺北・城市資訊", "http://stream.ginnet.cloud/live0130lo-yfyo/_definst_/fm/playlist.m3u8", 0},
    {"警廣臺北臺", "北部・交通路況", "http://stream.pbs.gov.tw:1935/live/TPS/playlist.m3u8", 0},
    {"警廣全國網", "全臺・交通新聞", "http://stream.pbs.gov.tw:1935/live/PBS/playlist.m3u8", 0},
#endif
};
