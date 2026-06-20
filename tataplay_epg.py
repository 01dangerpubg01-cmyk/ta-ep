#!/usr/bin/env python3
"""
TataPlay EPG Generator
Source: mitthu786/tvepg (tataplay/epg.xml.gz) — 890 channels, daily updated

Usage:
    python3 tataplay_epg.py                        # All channels
    python3 tataplay_epg.py --lang tamil            # Tamil only
    python3 tataplay_epg.py --lang tamil,telugu,malayalam,kannada
    python3 tataplay_epg.py --output epg.xml --gz
    python3 tataplay_epg.py --list-channels
    python3 tataplay_epg.py --list-channels --lang hindi
"""

import argparse
import gzip
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from xml.dom import minidom

EPG_URL = "https://raw.githubusercontent.com/mitthu786/tvepg/main/tataplay/epg.xml.gz"

# ── Channel map (890 channels — key ones listed, rest pass-through) ──
CHANNELS = {
    # Tamil
    "ts521":  {"name": "Sun TV HD",              "lang": "ta", "group": "Tamil"},
    "ts380":  {"name": "KTV HD",                 "lang": "ta", "group": "Tamil"},
    "ts474":  {"name": "Sun Life",               "lang": "ta", "group": "Tamil"},
    "ts199":  {"name": "Jaya Max",               "lang": "ta", "group": "Tamil"},
    "ts198":  {"name": "Jaya Plus",              "lang": "ta", "group": "Tamil"},
    "ts708":  {"name": "Jaya TV HD",             "lang": "ta", "group": "Tamil"},
    "ts200":  {"name": "Kalaignar TV",           "lang": "ta", "group": "Tamil"},
    "ts99":   {"name": "D Tamil",                "lang": "ta", "group": "Tamil"},
    "ts418":  {"name": "Colors Tamil",           "lang": "ta", "group": "Tamil"},
    "ts674":  {"name": "Colors Tamil HD",        "lang": "ta", "group": "Tamil"},
    "ts257":  {"name": "Zee Tamil",              "lang": "ta", "group": "Tamil"},
    "ts608":  {"name": "Zee Tamil HD",           "lang": "ta", "group": "Tamil"},
    "ts496":  {"name": "Star Vijay HD",          "lang": "ta", "group": "Tamil"},
    "ts220":  {"name": "Puthiya Thalaimurai",    "lang": "ta", "group": "Tamil"},
    "ts509":  {"name": "Polimer News",           "lang": "ta", "group": "Tamil"},
    "ts272":  {"name": "Polimer TV",             "lang": "ta", "group": "Tamil"},
    "ts524":  {"name": "Thanthi TV",             "lang": "ta", "group": "Tamil"},
    "ts1322": {"name": "Thanthi One",            "lang": "ta", "group": "Tamil"},
    "ts448":  {"name": "News7 Tamil",            "lang": "ta", "group": "Tamil"},
    "ts455":  {"name": "Sathiyam TV",            "lang": "ta", "group": "Tamil"},
    "ts392":  {"name": "Makkal TV",              "lang": "ta", "group": "Tamil"},
    "ts439":  {"name": "Raj TV",                 "lang": "ta", "group": "Tamil"},
    "ts425":  {"name": "Raj Musix Tamil",        "lang": "ta", "group": "Tamil"},
    "ts58":   {"name": "News18 Tamil Nadu",      "lang": "ta", "group": "Tamil"},
    "ts968":  {"name": "News Tamil 24x7",        "lang": "ta", "group": "Tamil"},
    "ts659":  {"name": "Vendhar TV",             "lang": "ta", "group": "Tamil"},
    "ts499":  {"name": "Vasanth TV",             "lang": "ta", "group": "Tamil"},
    "ts421":  {"name": "Peppers TV",             "lang": "ta", "group": "Tamil"},
    "ts1616": {"name": "Vikatan TV",             "lang": "ta", "group": "Tamil"},
    "ts647":  {"name": "Isaiaruvi",              "lang": "ta", "group": "Tamil"},
    "ts611":  {"name": "Sirippoli",              "lang": "ta", "group": "Tamil"},
    "ts1166": {"name": "Chithiram TV",           "lang": "ta", "group": "Tamil"},
    "ts1317": {"name": "Tamil Janam TV",         "lang": "ta", "group": "Tamil"},
    "ts411":  {"name": "Murasu TV",              "lang": "ta", "group": "Tamil"},

    # Telugu
    "ts355":  {"name": "Gemini TV HD",           "lang": "te", "group": "Telugu"},
    "ts362":  {"name": "Gemini Movies HD",       "lang": "te", "group": "Telugu"},
    "ts11":   {"name": "TV9 Telugu",             "lang": "te", "group": "Telugu"},
    "ts160":  {"name": "NTV Telugu",             "lang": "te", "group": "Telugu"},
    "ts250":  {"name": "Zee Telugu",             "lang": "te", "group": "Telugu"},
    "ts635":  {"name": "Zee Telugu HD",          "lang": "te", "group": "Telugu"},
    "ts252":  {"name": "Zee Cinemalu",           "lang": "te", "group": "Telugu"},
    "ts636":  {"name": "Zee Cinemalu HD",        "lang": "te", "group": "Telugu"},
    "ts83":   {"name": "ETV Telangana",          "lang": "te", "group": "Telugu"},
    "ts146":  {"name": "ETV Andhra Pradesh",     "lang": "te", "group": "Telugu"},
    "ts358":  {"name": "ETV Abhiruchi",          "lang": "te", "group": "Telugu"},
    "ts359":  {"name": "ETV HD",                 "lang": "te", "group": "Telugu"},
    "ts516":  {"name": "Star Maa HD",            "lang": "te", "group": "Telugu"},
    "ts957":  {"name": "Star Maa Movies HD",     "lang": "te", "group": "Telugu"},
    "ts596":  {"name": "Sakshi TV",              "lang": "te", "group": "Telugu"},
    "ts49":   {"name": "T News",                 "lang": "te", "group": "Telugu"},
    "ts274":  {"name": "V6 Telugu",              "lang": "te", "group": "Telugu"},
    "ts225":  {"name": "ABN Andhra Jyothy",      "lang": "te", "group": "Telugu"},
    "ts429":  {"name": "Raj Musix Telugu",       "lang": "te", "group": "Telugu"},
    "ts954":  {"name": "Star Maa Gold",          "lang": "te", "group": "Telugu"},
    "ts1288": {"name": "Zee Telugu News",        "lang": "te", "group": "Telugu"},
    "ts1100": {"name": "BIG TV Telugu",          "lang": "te", "group": "Telugu"},

    # Malayalam
    "ts292":  {"name": "Asianet HD",             "lang": "ml", "group": "Malayalam"},
    "ts293":  {"name": "Asianet Movies HD",      "lang": "ml", "group": "Malayalam"},
    "ts532":  {"name": "Asianet News",           "lang": "ml", "group": "Malayalam"},
    "ts953":  {"name": "Asianet Plus",           "lang": "ml", "group": "Malayalam"},
    "ts31":   {"name": "Mazhavil Manorama",      "lang": "ml", "group": "Malayalam"},
    "ts395":  {"name": "Mazhavil Manorama HD",   "lang": "ml", "group": "Malayalam"},
    "ts87":   {"name": "Manorama News",          "lang": "ml", "group": "Malayalam"},
    "ts229":  {"name": "Surya Movies",           "lang": "ml", "group": "Malayalam"},
    "ts230":  {"name": "Surya TV",               "lang": "ml", "group": "Malayalam"},
    "ts25":   {"name": "Kairali TV",             "lang": "ml", "group": "Malayalam"},
    "ts211":  {"name": "Kairali News",           "lang": "ml", "group": "Malayalam"},
    "ts576":  {"name": "Media One",              "lang": "ml", "group": "Malayalam"},
    "ts394":  {"name": "Mathrubhumi News",       "lang": "ml", "group": "Malayalam"},
    "ts178":  {"name": "Amrita TV",              "lang": "ml", "group": "Malayalam"},
    "ts270":  {"name": "Janam TV",               "lang": "ml", "group": "Malayalam"},
    "ts684":  {"name": "Zee Keralam",            "lang": "ml", "group": "Malayalam"},
    "ts694":  {"name": "Zee Keralam HD",         "lang": "ml", "group": "Malayalam"},
    "ts66":   {"name": "News18 Kerala",          "lang": "ml", "group": "Malayalam"},
    "ts799":  {"name": "Twenty Four",            "lang": "ml", "group": "Malayalam"},
    "ts377":  {"name": "Kappa TV",               "lang": "ml", "group": "Malayalam"},
    "ts378":  {"name": "Kaumudy TV",             "lang": "ml", "group": "Malayalam"},
    "ts10":   {"name": "Flowers TV",             "lang": "ml", "group": "Malayalam"},
    "ts1124": {"name": "Reporter TV",            "lang": "ml", "group": "Malayalam"},

    # Kannada
    "ts492":  {"name": "Udaya TV HD",            "lang": "kn", "group": "Kannada"},
    "ts231":  {"name": "Udaya Movies",           "lang": "kn", "group": "Kannada"},
    "ts629":  {"name": "TV5 Kannada",            "lang": "kn", "group": "Kannada"},
    "ts108":  {"name": "Colors Kannada",         "lang": "kn", "group": "Kannada"},
    "ts612":  {"name": "Colors Kannada HD",      "lang": "kn", "group": "Kannada"},
    "ts667":  {"name": "Colors Kannada Cinema",  "lang": "kn", "group": "Kannada"},
    "ts256":  {"name": "Zee Kannada",            "lang": "kn", "group": "Kannada"},
    "ts675":  {"name": "Zee Kannada HD",         "lang": "kn", "group": "Kannada"},
    "ts33":   {"name": "Public TV",              "lang": "kn", "group": "Kannada"},
    "ts342":  {"name": "R Kannada",              "lang": "kn", "group": "Kannada"},
    "ts85":   {"name": "News18 Kannada",         "lang": "kn", "group": "Kannada"},
    "ts152":  {"name": "TV9 Kannada",            "lang": "kn", "group": "Kannada"},
    "ts510":  {"name": "Raj News Kannada",       "lang": "kn", "group": "Kannada"},
    "ts427":  {"name": "Raj Musix Kannada",      "lang": "kn", "group": "Kannada"},
    "ts467":  {"name": "Star Suvarna HD",        "lang": "kn", "group": "Kannada"},
    "ts540":  {"name": "Star Suvarna Plus",      "lang": "kn", "group": "Kannada"},
    "ts913":  {"name": "News 1st Kannada",       "lang": "kn", "group": "Kannada"},
    "ts1287": {"name": "Zee Kannada News",       "lang": "kn", "group": "Kannada"},

    # Hindi
    "ts8":    {"name": "Star Plus HD",           "lang": "hi", "group": "Hindi"},
    "ts557":  {"name": "Zee TV",                 "lang": "hi", "group": "Hindi"},
    "ts63":   {"name": "Zee TV HD",              "lang": "hi", "group": "Hindi"},
    "ts543":  {"name": "Colors",                 "lang": "hi", "group": "Hindi"},
    "ts52":   {"name": "Colors HD",              "lang": "hi", "group": "Hindi"},
    "ts123":  {"name": "Zee Cinema",             "lang": "hi", "group": "Hindi"},
    "ts503":  {"name": "Zee Cinema HD",          "lang": "hi", "group": "Hindi"},
    "ts51":   {"name": "Dangal",                 "lang": "hi", "group": "Hindi"},
    "ts297":  {"name": "Big Magic",              "lang": "hi", "group": "Hindi"},
    "ts126":  {"name": "EPIC",                   "lang": "hi", "group": "Hindi"},
    "ts153":  {"name": "Aaj Tak",               "lang": "hi", "group": "Hindi News"},
    "ts689":  {"name": "Aaj Tak HD",            "lang": "hi", "group": "Hindi News"},
    "ts208":  {"name": "NDTV 24x7",             "lang": "hi", "group": "Hindi News"},
    "ts179":  {"name": "NDTV India",            "lang": "hi", "group": "Hindi News"},
    "ts72":   {"name": "Republic TV",           "lang": "hi", "group": "Hindi News"},
    "ts36":   {"name": "News Nation",           "lang": "hi", "group": "Hindi News"},
    "ts696":  {"name": "R Bharat",              "lang": "hi", "group": "Hindi News"},
    "ts1":    {"name": "India Today",           "lang": "hi", "group": "Hindi News"},

    # English
    "ts90":   {"name": "Times Now",             "lang": "en", "group": "English News"},
    "ts591":  {"name": "Mirror Now",            "lang": "en", "group": "English News"},
    "ts243":  {"name": "CNN International",     "lang": "en", "group": "English News"},
    "ts188":  {"name": "BBC News",              "lang": "en", "group": "English News"},
    "ts255":  {"name": "WION",                  "lang": "en", "group": "English News"},

    # Sports
    "ts78":   {"name": "Star Sports 1 HD",      "lang": "en", "group": "Sports"},
    "ts24":   {"name": "Star Sports 1 Hindi HD","lang": "hi", "group": "Sports"},
    "ts235":  {"name": "Star Sports 2 HD",      "lang": "en", "group": "Sports"},
    "ts246":  {"name": "Star Sports Select 1 HD","lang": "en","group": "Sports"},
    "ts223":  {"name": "DD Sports",             "lang": "hi", "group": "Sports"},
    "ts812":  {"name": "Eurosport HD",          "lang": "en", "group": "Sports"},

    # Kids
    "ts238":  {"name": "Cartoon Network",       "lang": "en", "group": "Kids"},
    "ts681":  {"name": "Cartoon Network HD+",   "lang": "en", "group": "Kids"},
    "ts138":  {"name": "Nick",                  "lang": "en", "group": "Kids"},
    "ts433":  {"name": "Nick HD+",              "lang": "en", "group": "Kids"},
    "ts239":  {"name": "Pogo",                  "lang": "en", "group": "Kids"},
    "ts119":  {"name": "Discovery Kids",        "lang": "en", "group": "Kids"},
    "ts816":  {"name": "CBeebies",              "lang": "en", "group": "Kids"},
}

LANG_MAP = {
    "tamil":"ta","telugu":"te","malayalam":"ml","kannada":"kn",
    "hindi":"hi","english":"en","sports":"sports","kids":"en",
}


def fetch_epg(url: str) -> bytes:
    print(f"[↓] Fetching {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (tataplay-epg/2.0)"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        gz = resp.read()
    xml_bytes = gzip.decompress(gz)
    print(f"[✓] {len(gz)//1024} KB gz → {len(xml_bytes)//1024} KB xml")
    return xml_bytes


def filter_and_build(xml_bytes: bytes, filter_ids: set, all_channels: bool = False) -> ET.Element:
    print("[*] Parsing XML ...")
    src = ET.fromstring(xml_bytes)

    out = ET.Element("tv")
    out.set("generator-info-name", "tataplay-epg")
    out.set("source-info-name", "TataPlay (via tvepg)")
    out.set("source-info-url", "https://www.tataplay.com")

    # Channels — use upstream data but override name/lang from our map
    found = set()
    for ch in src.findall("channel"):
        cid = ch.get("id", "")
        if cid not in filter_ids:
            continue
        found.add(cid)
        meta = CHANNELS.get(cid, {})

        new_ch = ET.SubElement(out, "channel")
        new_ch.set("id", cid)

        dn = ET.SubElement(new_ch, "display-name")
        dn.set("lang", meta.get("lang", "en"))
        dn.text = meta.get("name") or ch.findtext("display-name", cid)

        # Keep original icon
        orig_icon = ch.find("icon")
        if orig_icon is not None:
            ET.SubElement(new_ch, "icon").set("src", orig_icon.get("src", ""))

    # Programmes
    prog_count = 0
    for prog in src.findall("programme"):
        if prog.get("channel", "") in filter_ids:
            out.append(prog)
            prog_count += 1

    print(f"[✓] Channels: {len(found)}/{len(filter_ids)} | Programmes: {prog_count}")
    return out


def prettify(element: ET.Element) -> str:
    raw = ET.tostring(element, encoding="unicode")
    dom = minidom.parseString(raw)
    lines = dom.toprettyxml(indent="  ").split("\n")
    lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="TataPlay EPG Generator")
    parser.add_argument("--output", default="tataplay_epg.xml")
    parser.add_argument("--gz",     action="store_true")
    parser.add_argument("--lang",   default="", help="Filter: tamil,telugu,malayalam,kannada,hindi,english,sports,kids")
    parser.add_argument("--all",    action="store_true", help="Include ALL 890 channels (not just mapped ones)")
    parser.add_argument("--list-channels", action="store_true")
    args = parser.parse_args()

    if args.list_channels:
        groups = {}
        for cid, meta in CHANNELS.items():
            groups.setdefault(meta["group"], []).append((cid, meta["name"]))
        for grp in sorted(groups):
            print(f"\n── {grp} ──")
            for cid, name in groups[grp]:
                print(f"  {cid:<8} {name}")
        print(f"\nTotal: {len(CHANNELS)} mapped channels")
        return

    # Build filter set
    if args.all:
        # Fetch all channels from upstream file
        print("[*] Fetching all 890 channels ...")
        xml_bytes = fetch_epg(EPG_URL)
        src = ET.fromstring(xml_bytes)
        filter_ids = {ch.get("id","") for ch in src.findall("channel")}
    elif args.lang:
        langs = set()
        for l in args.lang.split(","):
            l = l.strip().lower()
            if l in LANG_MAP:
                langs.add(LANG_MAP[l])
            elif l == "sports":
                # Sports channels are mixed lang
                sports_ids = {cid for cid, m in CHANNELS.items() if m["group"] == "Sports"}
                filter_ids = sports_ids
        if langs:
            filter_ids = {cid for cid, m in CHANNELS.items() if m["lang"] in langs}
        print(f"[*] Filter: {args.lang} → {len(filter_ids)} channels")
        xml_bytes = fetch_epg(EPG_URL)
    else:
        filter_ids = set(CHANNELS.keys())
        print(f"[*] All mapped channels: {len(filter_ids)}")
        xml_bytes = fetch_epg(EPG_URL)

    root    = filter_and_build(xml_bytes, filter_ids)
    xml_str = prettify(root)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(f"[✓] Saved: {args.output} ({os.path.getsize(args.output)//1024} KB)")

    if args.gz:
        gz = args.output + ".gz"
        with gzip.open(gz, "wb") as f:
            f.write(xml_str.encode())
        print(f"[✓] Saved: {gz} ({os.path.getsize(gz)//1024} KB)")


if __name__ == "__main__":
    main()
