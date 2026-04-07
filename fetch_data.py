#!/usr/bin/env python3
"""
RAPTOR Alert v2.0
- KAMA veloce (n=5)  → trigger entrata
- KAMA lenta  (n=21) → stop base
- SAR Parabolico     → stop/conferma
- Stop  = MAX(KAMA lenta, SAR)
- Target = Entrata + (Entrata - Stop) * 2
- Storico segnali → data/history.json
- Mail novità tra run → Gmail SMTP
- Contatore run → data/stats.json
"""

import json, time, os, smtplib, math
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request

# ── Config ────────────────────────────────────────────────────────────────────
GMAIL_USER     = os.environ.get("GMAIL_USER", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD", "")
MAIL_TO        = os.environ.get("MAIL_TO", "")
NOW            = datetime.now().strftime("%d/%m/%Y %H:%M")
NOW_DATE       = datetime.now().strftime("%d/%m/%Y")
NOW_TIME       = datetime.now().strftime("%H:%M")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

# ── Tickers (solo Europa) ─────────────────────────────────────────────────────
TICKERS = [
    {"y":"IAEX.AS","c":"Paesi","t":"IAEX"},{"y":"TOF.AS","c":"ATTIVO","t":"TOF"},
    {"y":"18MN.DE","c":"Lazy","t":"18MN"},{"y":"7USH.DE","c":"BOND","t":"7USH"},
    {"y":"CBUH.DE","c":"ATTIVO","t":"CBUH"},{"y":"CEB1.DE","c":"BOND","t":"CEB1"},
    {"y":"CEB4.DE","c":"NEW AREA","t":"CEB4"},{"y":"DBZB.DE","c":"Lazy","t":"DBZB"},
    {"y":"EUNY.DE","c":"ATTIVO","t":"EUNY"},{"y":"FTGM.DE","c":"ATTIVO","t":"FTGM"},
    {"y":"IBC5.DE","c":"BOND","t":"IBC5"},{"y":"IBCJ.DE","c":"Paesi","t":"IBCJ"},
    {"y":"IQQ9.DE","c":"NEW AREA","t":"IQQ9"},{"y":"IQQF.DE","c":"NEW AREA","t":"IQQF"},
    {"y":"IS04.DE","c":"BOND","t":"IS04"},{"y":"IS3C.DE","c":"Lazy","t":"IS3C"},
    {"y":"IS3N.DE","c":"Lazy","t":"IS3N"},{"y":"IS3U.DE","c":"Paesi","t":"IS3U"},
    {"y":"ISPA.DE","c":"ATTIVO","t":"ISPA"},{"y":"IUSQ.DE","c":"Lazy","t":"IUSQ"},
    {"y":"IUSS.DE","c":"Paesi","t":"IUSS"},{"y":"LCUJ.DE","c":"Lazy","t":"LCUJ"},
    {"y":"MJMT.DE","c":"ATTIVO","t":"MJMT"},{"y":"QDVA.DE","c":"ATTIVO","t":"QDVA"},
    {"y":"SPP5.DE","c":"BOND","t":"SPP5"},{"y":"SPYX.DE","c":"ATTIVO","t":"SPYX"},
    {"y":"SXR1.DE","c":"Lazy","t":"SXR1"},{"y":"SXRT.DE","c":"Lazy","t":"SXRT"},
    {"y":"SXRU.DE","c":"NEW AREA","t":"SXRU"},{"y":"SXRW.DE","c":"Lazy","t":"SXRW"},
    {"y":"VGWE.DE","c":"ATTIVO","t":"VGWE"},{"y":"VUKG.DE","c":"Paesi","t":"VUKG"},
    {"y":"XBAS.DE","c":"Paesi","t":"XBAS"},{"y":"XCS3.DE","c":"Paesi","t":"XCS3"},
    {"y":"XCS4.DE","c":"Paesi","t":"XCS4"},{"y":"XD9E.DE","c":"Lazy","t":"XD9E"},
    {"y":"XD9U.DE","c":"Lazy","t":"XD9U"},{"y":"XDEM.DE","c":"ATTIVO","t":"XDEM"},
    {"y":"XESD.DE","c":"Paesi","t":"XESD"},{"y":"XGIN.DE","c":"Lazy","t":"XGIN"},
    {"y":"XMKA.DE","c":"Paesi","t":"XMKA"},{"y":"XPQP.DE","c":"Paesi","t":"XPQP"},
    {"y":"XWEM.DE","c":"ATTIVO","t":"XWEM"},{"y":"F701.F","c":"ATTIVO","t":"F701"},
    {"y":"F702.F","c":"ATTIVO","t":"F702"},{"y":"F703.F","c":"ATTIVO","t":"F703"},
    {"y":"IUSN.F","c":"ADVICE","t":"IUSN"},{"y":"IVAI.MI","c":"Tematici","t":"IVAI"},
    {"y":"IVDF.DE","c":"Tematici","t":"IVDF"},{"y":"NQSE.F","c":"NEW AREA","t":"NQSE"},
    {"y":"NTSZ.DE","c":"ATTIVO","t":"NTSZ"},{"y":"IEFM.L","c":"ATTIVO","t":"IEFM"},
    {"y":"A01U.MI","c":"BOND","t":"A01U"},{"y":"ACT20.MI","c":"ATTIVO","t":"ACT20"},
    {"y":"ACT60.MI","c":"ATTIVO","t":"ACT60"},{"y":"ACTEQ.MI","c":"ATTIVO","t":"ACTEQ"},
    {"y":"ADLU.MI","c":"BOND","t":"ADLU"},{"y":"AEGE.MI","c":"BOND","t":"AEGE"},
    {"y":"AGEB.MI","c":"BOND","t":"AGEB"},{"y":"AGED.MI","c":"Tematici","t":"AGED"},
    {"y":"AGGH.MI","c":"BOND","t":"AGGH"},{"y":"AI4UJ.MI","c":"Tematici","t":"AI4UJ"},
    {"y":"AIAA.MI","c":"Tematici","t":"AIAA"},{"y":"AIAI.MI","c":"Tematici","t":"AIAI"},
    {"y":"AICU.MI","c":"BOND","t":"AICU"},{"y":"AIGA.MI","c":"Materie","t":"AIGA"},
    {"y":"AIGC.MI","c":"Materie","t":"AIGC"},{"y":"AIGE.MI","c":"Materie","t":"AIGE"},
    {"y":"AIGG.MI","c":"Materie","t":"AIGG"},{"y":"AIGI.MI","c":"Materie","t":"AIGI"},
    {"y":"AIGL.MI","c":"Materie","t":"AIGL"},{"y":"AIGO.MI","c":"Materie","t":"AIGO"},
    {"y":"AIGP.MI","c":"Materie","t":"AIGP"},{"y":"AIGS.MI","c":"Materie","t":"AIGS"},
    {"y":"AINF.MI","c":"Tematici","t":"AINF"},{"y":"AIQE.MI","c":"Tematici","t":"AIQE"},
    {"y":"ALAT.MI","c":"NEW AREA","t":"ALAT"},{"y":"ALUM.MI","c":"Materie","t":"ALUM"},
    {"y":"ANAU.MI","c":"ADVICE","t":"ANAU"},{"y":"AQWA.MI","c":"Tematici","t":"AQWA"},
    {"y":"ARMI.MI","c":"Tematici","t":"ARMI"},{"y":"ARMR.MI","c":"Tematici","t":"ARMR"},
    {"y":"ASRD.MI","c":"BOND","t":"ASRD"},{"y":"AT1.MI","c":"BOND","t":"AT1"},
    {"y":"AUCO.MI","c":"Tematici","t":"AUCO"},{"y":"AUHEUA.MI","c":"Paesi","t":"AUHEUA"},
    {"y":"BATT.MI","c":"Tematici","t":"BATT"},{"y":"BBTR.MI","c":"BOND","t":"BBTR"},
    {"y":"BCHN.MI","c":"Settoriali","t":"BCHN"},{"y":"BENE.MI","c":"Materie","t":"BENE"},
    {"y":"BIODV.MI","c":"Settoriali","t":"BIODV"},{"y":"BIOT.MI","c":"Tematici","t":"BIOT"},
    {"y":"BKCH.MI","c":"Tematici","t":"BKCH"},{"y":"BLTH.MI","c":"Tematici","t":"BLTH"},
    {"y":"BNK.MI","c":"Settoriali","t":"BNK"},{"y":"BNKE.MI","c":"Settoriali","t":"BNKE"},
    {"y":"BOTZ.MI","c":"Tematici","t":"BOTZ"},{"y":"BRENT.MI","c":"Materie","t":"BRENT"},
    {"y":"BRES.MI","c":"Settoriali","t":"BRES"},{"y":"BRIJ.MI","c":"Tematici","t":"BRIJ"},
    {"y":"BRND.MI","c":"Materie","t":"BRND"},{"y":"BRNT.MI","c":"Materie","t":"BRNT"},
    {"y":"BTC.MI","c":"Tematici","t":"BTC"},{"y":"BTECH.MI","c":"Tematici","t":"BTECH"},
    {"y":"BTP10.MI","c":"BOND","t":"BTP10"},{"y":"BUG.MI","c":"Tematici","t":"BUG"},
    {"y":"C40.MI","c":"Paesi","t":"C40"},{"y":"CARB.MI","c":"Materie","t":"CARB"},
    {"y":"CAUT.MI","c":"Tematici","t":"CAUT"},{"y":"CBSUSA.MI","c":"BOND","t":"CBSUSA"},
    {"y":"CHIP.MI","c":"ADVICE","t":"CHIP"},{"y":"CHM.MI","c":"Settoriali","t":"CHM"},
    {"y":"CIBR.MI","c":"ADVICE","t":"CIBR"},{"y":"CIT.MI","c":"Tematici","t":"CIT"},
    {"y":"CLIP.MI","c":"BOND","t":"CLIP"},{"y":"CLOU.MI","c":"Tematici","t":"CLOU"},
    {"y":"CN1.MI","c":"Paesi","t":"CN1"},{"y":"CO2.MI","c":"Materie","t":"CO2"},
    {"y":"COFF.MI","c":"Materie","t":"COFF"},{"y":"COMO.MI","c":"Materie","t":"COMO"},
    {"y":"COPA.MI","c":"Materie","t":"COPA"},{"y":"COPM.MI","c":"Tematici","t":"COPM"},
    {"y":"COPX.MI","c":"Tematici","t":"COPX"},{"y":"CORN.MI","c":"Materie","t":"CORN"},
    {"y":"CROP.MI","c":"Tematici","t":"CROP"},{"y":"CRUD.MI","c":"Materie","t":"CRUD"},
    {"y":"CSSPX.MI","c":"ADVICE","t":"CSSPX"},{"y":"CSUS.MI","c":"ADVICE","t":"CSUS"},
    {"y":"CTEK.MI","c":"Tematici","t":"CTEK"},{"y":"CURE.MI","c":"Tematici","t":"CURE"},
    {"y":"CYBR.MI","c":"Settoriali","t":"CYBR"},{"y":"DAPP.MI","c":"Tematici","t":"DAPP"},
    {"y":"DEFS.MI","c":"Settoriali","t":"DEFS"},{"y":"DFNS.MI","c":"Tematici","t":"DFNS"},
    {"y":"DJE.MI","c":"Paesi","t":"DJE"},{"y":"DMAT.MI","c":"Tematici","t":"DMAT"},
    {"y":"DOCT.MI","c":"Tematici","t":"DOCT"},{"y":"DRVE.MI","c":"Tematici","t":"DRVE"},
    {"y":"DXJF.MI","c":"ATTIVO","t":"DXJF"},{"y":"EBIZ.MI","c":"Tematici","t":"EBIZ"},
    {"y":"EBUY.MI","c":"Tematici","t":"EBUY"},{"y":"ECAR.MI","c":"Tematici","t":"ECAR"},
    {"y":"ECO.MI","c":"BOND","t":"ECO"},{"y":"ECOM.MI","c":"Tematici","t":"ECOM"},
    {"y":"ECR1.MI","c":"BOND","t":"ECR1"},{"y":"EDOC.MI","c":"Tematici","t":"EDOC"},
    {"y":"EEA.MI","c":"Tematici","t":"EEA"},{"y":"EEIA.MI","c":"ATTIVO","t":"EEIA"},
    {"y":"EENG.MI","c":"Settoriali","t":"EENG"},{"y":"EGOV.MI","c":"BOND","t":"EGOV"},
    {"y":"EHYA.MI","c":"BOND","t":"EHYA"},{"y":"EIMI.MI","c":"ADVICE","t":"EIMI"},
    {"y":"ELCR.MI","c":"Tematici","t":"ELCR"},{"y":"EMI.MI","c":"BOND","t":"EMI"},
    {"y":"EMOVE.MI","c":"Tematici","t":"EMOVE"},{"y":"EMQQ.MI","c":"Settoriali","t":"EMQQ"},
    {"y":"ENCO.MI","c":"Materie","t":"ENCO"},{"y":"ENRG.MI","c":"Settoriali","t":"ENRG"},
    {"y":"EPRA.MI","c":"Tematici","t":"EPRA"},{"y":"EPRE.MI","c":"Tematici","t":"EPRE"},
    {"y":"EROX.MI","c":"ADVICE","t":"EROX"},{"y":"ESGO.MI","c":"Tematici","t":"ESGO"},
    {"y":"ESPO.MI","c":"Tematici","t":"ESPO"},{"y":"ESPY.MI","c":"Tematici","t":"ESPY"},
    {"y":"EST.MI","c":"NEW AREA","t":"EST"},{"y":"EUC.MI","c":"BOND","t":"EUC"},
    {"y":"EXS1.MI","c":"Paesi","t":"EXS1"},{"y":"EXXY.MI","c":"Materie","t":"EXXY"},
    {"y":"FINX.MI","c":"Tematici","t":"FINX"},{"y":"FLXI.MI","c":"Paesi","t":"FLXI"},
    {"y":"FMI.MI","c":"Paesi","t":"FMI"},{"y":"FOO.MI","c":"Settoriali","t":"FOO"},
    {"y":"FOOD.MI","c":"Settoriali","t":"FOOD"},{"y":"FUSU.MI","c":"ATTIVO","t":"FUSU"},
    {"y":"GAGG.MI","c":"BOND","t":"GAGG"},{"y":"GAS.MI","c":"Materie","t":"GAS"},
    {"y":"GCLE.MI","c":"Tematici","t":"GCLE"},{"y":"GDX.MI","c":"Tematici","t":"GDX"},
    {"y":"GDXJ.MI","c":"Tematici","t":"GDXJ"},{"y":"GLUX.MI","c":"Tematici","t":"GLUX"},
    {"y":"GNOM.MI","c":"Tematici","t":"GNOM"},{"y":"GOAI.MI","c":"Tematici","t":"GOAI"},
    {"y":"GOVA.MI","c":"BOND","t":"GOVA"},{"y":"GRC.MI","c":"Paesi","t":"GRC"},
    {"y":"GSCE.MI","c":"Materie","t":"GSCE"},{"y":"GSM.MI","c":"Tematici","t":"GSM"},
    {"y":"HDRO.MI","c":"Tematici","t":"HDRO"},{"y":"HEAL.MI","c":"Tematici","t":"HEAL"},
    {"y":"HERU.MI","c":"Tematici","t":"HERU"},{"y":"HLT.MI","c":"Settoriali","t":"HLT"},
    {"y":"HTWO.MI","c":"Tematici","t":"HTWO"},{"y":"HYGN.MI","c":"Tematici","t":"HYGN"},
    {"y":"HYLD.MI","c":"ADVICE","t":"HYLD"},{"y":"IAPD.MI","c":"NEW AREA","t":"IAPD"},
    {"y":"IBZL.MI","c":"Paesi","t":"IBZL"},{"y":"ICBR.MI","c":"Tematici","t":"ICBR"},
    {"y":"IEAA.MI","c":"BOND","t":"IEAA"},{"y":"IEGS.MI","c":"BOND","t":"IEGS"},
    {"y":"IEMB.MI","c":"ADVICE","t":"IEMB"},{"y":"IEMO.MI","c":"ATTIVO","t":"IEMO"},
    {"y":"IMIB.MI","c":"Paesi","t":"IMIB"},{"y":"INDG.MI","c":"Settoriali","t":"INDG"},
    {"y":"INDI.MI","c":"Paesi","t":"INDI"},{"y":"INF1A.MI","c":"BOND","t":"INF1A"},
    {"y":"INQQ.MI","c":"Tematici","t":"INQQ"},{"y":"INS.MI","c":"Settoriali","t":"INS"},
    {"y":"ISAC.MI","c":"NEW AREA","t":"ISAC"},{"y":"ISAG.MI","c":"Tematici","t":"ISAG"},
    {"y":"ISPY.MI","c":"Tematici","t":"ISPY"},{"y":"ITBL.MI","c":"Paesi","t":"ITBL"},
    {"y":"IU0E.MI","c":"BOND","t":"IU0E"},{"y":"IUSE.MI","c":"NEW AREA","t":"IUSE"},
    {"y":"IWDE.MI","c":"NEW AREA","t":"IWDE"},{"y":"IWMO.MI","c":"ATTIVO","t":"IWMO"},
    {"y":"IWVL.MI","c":"ADVICE","t":"IWVL"},{"y":"JEDI.MI","c":"Tematici","t":"JEDI"},
    {"y":"JRGE.MI","c":"NEW AREA","t":"JRGE"},{"y":"JU13.MI","c":"BOND","t":"JU13"},
    {"y":"KARS.MI","c":"Settoriali","t":"KARS"},{"y":"KOR.MI","c":"Paesi","t":"KOR"},
    {"y":"KRBN.MI","c":"Materie","t":"KRBN"},{"y":"KWBE.MI","c":"Tematici","t":"KWBE"},
    {"y":"LABL.MI","c":"Tematici","t":"LABL"},{"y":"LAFRI.MI","c":"NEW AREA","t":"LAFRI"},
    {"y":"LCCN.MI","c":"Paesi","t":"LCCN"},{"y":"LEAD.MI","c":"Materie","t":"LEAD"},
    {"y":"LITM.MI","c":"Tematici","t":"LITM"},{"y":"LITU.MI","c":"Tematici","t":"LITU"},
    {"y":"LOCK.MI","c":"Tematici","t":"LOCK"},{"y":"LTAM.MI","c":"NEW AREA","t":"LTAM"},
    {"y":"MACV.MI","c":"ATTIVO","t":"MACV"},{"y":"MAGR.MI","c":"ATTIVO","t":"MAGR"},
    {"y":"MATW.MI","c":"Settoriali","t":"MATW"},{"y":"MCHT.MI","c":"Tematici","t":"MCHT"},
    {"y":"METAA.MI","c":"Tematici","t":"METAA"},{"y":"METE.MI","c":"Tematici","t":"METE"},
    {"y":"MILL.MI","c":"Tematici","t":"MILL"},{"y":"MODR.MI","c":"ATTIVO","t":"MODR"},
    {"y":"NATO.MI","c":"Settoriali","t":"NATO"},{"y":"NCLR.MI","c":"Tematici","t":"NCLR"},
    {"y":"NGAS.MI","c":"Materie","t":"NGAS"},{"y":"NICK.MI","c":"Materie","t":"NICK"},
    {"y":"NTSG.MI","c":"ATTIVO","t":"NTSG"},{"y":"NUCL.MI","c":"Tematici","t":"NUCL"},
    {"y":"OCEAN.MI","c":"Settoriali","t":"OCEAN"},{"y":"OIH.MI","c":"Tematici","t":"OIH"},
    {"y":"OVER.MI","c":"BOND","t":"OVER"},{"y":"PAVE.MI","c":"Tematici","t":"PAVE"},
    {"y":"PHAG.MI","c":"Materie","t":"PHAG"},{"y":"PHPT.MI","c":"Materie","t":"PHPT"},
    {"y":"QNTM.MI","c":"Tematici","t":"QNTM"},{"y":"QTOP.MI","c":"Paesi","t":"QTOP"},
    {"y":"RARE.MI","c":"Tematici","t":"RARE"},{"y":"RAYZ.MI","c":"Tematici","t":"RAYZ"},
    {"y":"RBOT.MI","c":"ADVICE","t":"RBOT"},{"y":"REMX.MI","c":"Tematici","t":"REMX"},
    {"y":"RENW.MI","c":"Tematici","t":"RENW"},{"y":"REUSE.MI","c":"Settoriali","t":"REUSE"},
    {"y":"ROBO.MI","c":"Tematici","t":"ROBO"},{"y":"ROE.MI","c":"Tematici","t":"ROE"},
    {"y":"SAUDI.MI","c":"Paesi","t":"SAUDI"},{"y":"SBIO.MI","c":"Settoriali","t":"SBIO"},
    {"y":"SCITY.MI","c":"Tematici","t":"SCITY"},{"y":"SEMA.MI","c":"NEW AREA","t":"SEMA"},
    {"y":"SEME.MI","c":"Tematici","t":"SEME"},{"y":"SGBS.MI","c":"Materie","t":"SGBS"},
    {"y":"SILV.MI","c":"Tematici","t":"SILV"},{"y":"SJPA.MI","c":"NEW AREA","t":"SJPA"},
    {"y":"SMCX.MI","c":"ADVICE","t":"SMCX"},{"y":"SMEA.MI","c":"ADVICE","t":"SMEA"},
    {"y":"SMH.MI","c":"Tematici","t":"SMH"},{"y":"SNSR.MI","c":"Tematici","t":"SNSR"},
    {"y":"SOLR.MI","c":"Tematici","t":"SOLR"},{"y":"SP1E.MI","c":"Paesi","t":"SP1E"},
    {"y":"SP5A.MI","c":"ADVICE","t":"SP5A"},{"y":"SPXE.MI","c":"Paesi","t":"SPXE"},
    {"y":"SRIUC.MI","c":"BOND","t":"SRIUC"},{"y":"SRSA.MI","c":"Paesi","t":"SRSA"},
    {"y":"STAW.MI","c":"Settoriali","t":"STAW"},{"y":"DFSV.DE","c":"Settoriali SPDR","t":"DFSV"},
    {"y":"STKX.MI","c":"Settoriali SPDR","t":"STKX"},{"y":"STNX.MI","c":"Settoriali SPDR","t":"STNX"},
    {"y":"STPX.MI","c":"Settoriali SPDR","t":"STPX"},{"y":"STQX.MI","c":"Settoriali SPDR","t":"STQX"},
    {"y":"STRX.MI","c":"Settoriali SPDR","t":"STRX"},{"y":"STSX.MI","c":"Settoriali SPDR","t":"STSX"},
    {"y":"STTX.MI","c":"Settoriali SPDR","t":"STTX"},{"y":"STUX.MI","c":"Settoriali SPDR","t":"STUX"},
    {"y":"SUGA.MI","c":"Materie","t":"SUGA"},{"y":"SWDA.MI","c":"ADVICE","t":"SWDA"},
    {"y":"SXLB.MI","c":"Settoriali SPDR","t":"SXLB"},{"y":"SXLC.MI","c":"Settoriali SPDR","t":"SXLC"},
    {"y":"SXLF.MI","c":"Settoriali SPDR","t":"SXLF"},{"y":"SXLI.MI","c":"Settoriali SPDR","t":"SXLI"},
    {"y":"SXLK.MI","c":"Settoriali SPDR","t":"SXLK"},{"y":"SXLP.MI","c":"Settoriali SPDR","t":"SXLP"},
    {"y":"SXLU.MI","c":"Settoriali SPDR","t":"SXLU"},{"y":"SXLV.MI","c":"Settoriali SPDR","t":"SXLV"},
    {"y":"SXLY.MI","c":"Settoriali SPDR","t":"SXLY"},{"y":"T10A.MI","c":"BOND","t":"T10A"},
    {"y":"TELE.MI","c":"Settoriali","t":"TELE"},{"y":"TIP1A.MI","c":"BOND","t":"TIP1A"},
    {"y":"TLCO.MI","c":"Tematici","t":"TLCO"},{"y":"TNO.MI","c":"Settoriali","t":"TNO"},
    {"y":"TRVL.MI","c":"Settoriali","t":"TRVL"},{"y":"TUR.MI","c":"Paesi","t":"TUR"},
    {"y":"U3O8.MI","c":"Tematici","t":"U3O8"},{"y":"UCRP.MI","c":"BOND","t":"UCRP"},
    {"y":"UGAS.MI","c":"Materie","t":"UGAS"},{"y":"UKE.MI","c":"Paesi","t":"UKE"},
    {"y":"UNIC.MI","c":"Tematici","t":"UNIC"},{"y":"URNJ.MI","c":"Tematici","t":"URNJ"},
    {"y":"URNU.MI","c":"ADVICE","t":"URNU"},{"y":"US1.MI","c":"BOND","t":"US1"},
    {"y":"US10C.MI","c":"BOND","t":"US10C"},{"y":"US7.MI","c":"BOND","t":"US7"},
    {"y":"USIG.MI","c":"BOND","t":"USIG"},{"y":"USTEC.MI","c":"Tematici","t":"USTEC"},
    {"y":"UTI.MI","c":"Settoriali","t":"UTI"},{"y":"VAGF.MI","c":"BOND","t":"VAGF"},
    {"y":"VCDE.MI","c":"BOND","t":"VCDE"},{"y":"VDCA.MI","c":"BOND","t":"VDCA"},
    {"y":"VDCE.MI","c":"BOND","t":"VDCE"},{"y":"VDEA.MI","c":"BOND","t":"VDEA"},
    {"y":"VDST.MI","c":"BOND","t":"VDST"},{"y":"VECA.MI","c":"BOND","t":"VECA"},
    {"y":"VEGI.MI","c":"Tematici","t":"VEGI"},{"y":"VGEA.MI","c":"BOND","t":"VGEA"},
    {"y":"VITA.MI","c":"Settoriali","t":"VITA"},{"y":"VJPE.MI","c":"Paesi","t":"VJPE"},
    {"y":"VNGA20.MI","c":"ATTIVO","t":"VNGA20"},{"y":"VNGA40.MI","c":"ATTIVO","t":"VNGA40"},
    {"y":"VNGA60.MI","c":"ATTIVO","t":"VNGA60"},{"y":"VNGA80.MI","c":"ATTIVO","t":"VNGA80"},
    {"y":"VOLT.MI","c":"Tematici","t":"VOLT"},{"y":"VPN.MI","c":"Tematici","t":"VPN"},
    {"y":"VSCF.MI","c":"BOND","t":"VSCF"},{"y":"VSGF.MI","c":"BOND","t":"VSGF"},
    {"y":"VUCE.MI","c":"BOND","t":"VUCE"},{"y":"VUKE.MI","c":"Paesi","t":"VUKE"},
    {"y":"VUSA.MI","c":"Paesi","t":"VUSA"},{"y":"WATC.MI","c":"Tematici","t":"WATC"},
    {"y":"WATT.MI","c":"Materie","t":"WATT"},{"y":"WBLK.MI","c":"Tematici","t":"WBLK"},
    {"y":"WCBR.MI","c":"Tematici","t":"WCBR"},{"y":"WCLD.MI","c":"Settoriali","t":"WCLD"},
    {"y":"WDEF.MI","c":"Tematici","t":"WDEF"},{"y":"WDNA.MI","c":"Tematici","t":"WDNA"},
    {"y":"WEAT.MI","c":"Materie","t":"WEAT"},{"y":"WEB3.MI","c":"Tematici","t":"WEB3"},
    {"y":"WENT.MI","c":"Materie","t":"WENT"},{"y":"WFIN.MI","c":"Settoriali SPDR","t":"WFIN"},
    {"y":"WGRO.MI","c":"Tematici","t":"WGRO"},{"y":"WHEA.MI","c":"Settoriali SPDR","t":"WHEA"},
    {"y":"WIND.MI","c":"Settoriali SPDR","t":"WIND"},{"y":"WMAT.MI","c":"Settoriali SPDR","t":"WMAT"},
    {"y":"WMGT.MI","c":"Tematici","t":"WMGT"},{"y":"WMIB.MI","c":"Paesi","t":"WMIB"},
    {"y":"WNAS.MI","c":"Paesi","t":"WNAS"},{"y":"WNDE.MI","c":"Tematici","t":"WNDE"},
    {"y":"WNDY.MI","c":"Tematici","t":"WNDY"},{"y":"WNRG.MI","c":"Settoriali SPDR","t":"WNRG"},
    {"y":"WRNW.MI","c":"Tematici","t":"WRNW"},{"y":"WRTY.MI","c":"Paesi","t":"WRTY"},
    {"y":"WS5X.MI","c":"Paesi","t":"WS5X"},{"y":"WSLV.MI","c":"Tematici","t":"WSLV"},
    {"y":"WSPE.MI","c":"Paesi","t":"WSPE"},{"y":"WTAI.MI","c":"Tematici","t":"WTAI"},
    {"y":"WTEC.MI","c":"Settoriali SPDR","t":"WTEC"},{"y":"WTEL.MI","c":"Settoriali SPDR","t":"WTEL"},
    {"y":"WTI.MI","c":"Materie","t":"WTI"},{"y":"WTRE.MI","c":"Tematici","t":"WTRE"},
    {"y":"WUTI.MI","c":"Settoriali SPDR","t":"WUTI"},{"y":"X25E.MI","c":"BOND","t":"X25E"},
    {"y":"XAGZ.MI","c":"Materie","t":"XAGZ"},{"y":"XAIX.MI","c":"ADVICE","t":"XAIX"},
    {"y":"XBAE.MI","c":"BOND","t":"XBAE"},{"y":"XBAG.MI","c":"BOND","t":"XBAG"},
    {"y":"XBLC.MI","c":"BOND","t":"XBLC"},{"y":"XBNK.MI","c":"BOND","t":"XBNK"},
    {"y":"XCHA.MI","c":"Paesi","t":"XCHA"},{"y":"XCS5.MI","c":"Paesi","t":"XCS5"},
    {"y":"XCTE.MI","c":"Tematici","t":"XCTE"},{"y":"XDAX.MI","c":"Paesi","t":"XDAX"},
    {"y":"XDBC.MI","c":"Materie","t":"XDBC"},{"y":"XDEE.MI","c":"NEW AREA","t":"XDEE"},
    {"y":"XDER.MI","c":"Tematici","t":"XDER"},{"y":"XDEV.MI","c":"ADVICE","t":"XDEV"},
    {"y":"XDG3.MI","c":"Tematici","t":"XDG3"},{"y":"XDG6.MI","c":"Tematici","t":"XDG6"},
    {"y":"XDG7.MI","c":"Tematici","t":"XDG7"},{"y":"XDGI.MI","c":"Tematici","t":"XDGI"},
    {"y":"XDRE.MI","c":"Settoriali","t":"XDRE"},{"y":"XDW0.MI","c":"Settoriali","t":"XDW0"},
    {"y":"XDWC.MI","c":"Settoriali","t":"XDWC"},{"y":"XDWF.MI","c":"Settoriali","t":"XDWF"},
    {"y":"XDWH.MI","c":"Settoriali","t":"XDWH"},{"y":"XDWI.MI","c":"Settoriali","t":"XDWI"},
    {"y":"XDWM.MI","c":"Settoriali","t":"XDWM"},{"y":"XDWS.MI","c":"Settoriali","t":"XDWS"},
    {"y":"XDWT.MI","c":"Settoriali","t":"XDWT"},{"y":"XDWU.MI","c":"Settoriali","t":"XDWU"},
    {"y":"XE01.MI","c":"BOND","t":"XE01"},{"y":"XEON.MI","c":"Liquidità","t":"XEON"},
    {"y":"XFNT.MI","c":"Tematici","t":"XFNT"},{"y":"XFVT.MI","c":"Paesi","t":"XFVT"},
    {"y":"XG11.MI","c":"Tematici","t":"XG11"},{"y":"XG12.MI","c":"Tematici","t":"XG12"},
    {"y":"XGEN.MI","c":"Tematici","t":"XGEN"},{"y":"XGLE.MI","c":"BOND","t":"XGLE"},
    {"y":"XIFE.MI","c":"Settoriali","t":"XIFE"},{"y":"XLBS.MI","c":"Settoriali","t":"XLBS"},
    {"y":"XLCS.MI","c":"Settoriali","t":"XLCS"},{"y":"XLES.MI","c":"Settoriali","t":"XLES"},
    {"y":"XLFS.MI","c":"Settoriali","t":"XLFS"},{"y":"XLIS.MI","c":"Settoriali","t":"XLIS"},
    {"y":"XLKS.MI","c":"Settoriali","t":"XLKS"},{"y":"XLPE.MI","c":"Tematici","t":"XLPE"},
    {"y":"XLPS.MI","c":"Settoriali","t":"XLPS"},{"y":"XLUS.MI","c":"Settoriali","t":"XLUS"},
    {"y":"XLVS.MI","c":"Settoriali","t":"XLVS"},{"y":"XLYS.MI","c":"Settoriali","t":"XLYS"},
    {"y":"D5BI.DE","c":"Paesi","t":"D5BI"},{"y":"XMME.MI","c":"ADVICE","t":"XMME"},
    {"y":"XMOV.MI","c":"Tematici","t":"XMOV"},{"y":"XNGI.MI","c":"Tematici","t":"XNGI"},
    {"y":"XNNV.MI","c":"Tematici","t":"XNNV"},{"y":"XQUI.MI","c":"ATTIVO","t":"XQUI"},
    {"y":"XRES.MI","c":"Tematici","t":"XRES"},{"y":"XS8R.MI","c":"Tematici","t":"XS8R"},
    {"y":"XSFR.MI","c":"Paesi","t":"XSFR"},{"y":"XSGI.MI","c":"Tematici","t":"XSGI"},
    {"y":"XSMI.MI","c":"Paesi","t":"XSMI"},{"y":"XSX6.MI","c":"ADVICE","t":"XSX6"},
    {"y":"XT01.MI","c":"BOND","t":"XT01"},{"y":"XTC5.MI","c":"BOND","t":"XTC5"},
    {"y":"XTIP.MI","c":"BOND","t":"XTIP"},{"y":"XUSA.MI","c":"ATTIVO","t":"XUSA"},
    {"y":"XUTC.MI","c":"Settoriali","t":"XUTC"},{"y":"XWTS.MI","c":"Settoriali","t":"XWTS"},
    {"y":"XXSC.MI","c":"ATTIVO","t":"XXSC"},{"y":"XYP0.MI","c":"BOND","t":"XYP0"},
    {"y":"ZINC.MI","c":"Materie","t":"ZINC"},{"y":"DBMFE.PA","c":"ATTIVO","t":"DBMFE"},
    {"y":"MEUD.PA","c":"NEW AREA","t":"MEUD"},{"y":"WRD.PA","c":"Paesi","t":"WRD"},
    {"y":"IB01.SW","c":"BOND","t":"IB01"},{"y":"SDGPEX.SW","c":"ATTIVO","t":"SDGPEX"},
    {"y":"X13E.MI","c":"Liquidità","t":"X13E"},{"y":"EM13.MI","c":"Liquidità","t":"EM13"},
    {"y":"ERNE.MI","c":"Liquidità","t":"ERNE"},{"y":"INFR.MI","c":"REAL ESTATE","t":"INFR"},
    {"y":"XDWD.MI","c":"Benchmark","t":"XDWD"},{"y":"CW8.MI","c":"Benchmark","t":"CW8"},
    {"y":"IMEU.MI","c":"Benchmark","t":"IMEU"},{"y":"INAA.MI","c":"Benchmark","t":"INAA"},
    {"y":"SXLE.MI","c":"Settoriali SPDR","t":"SXLE"},{"y":"MGIN.MI","c":"Settoriali SPDR","t":"MGIN"},
    {"y":"STWX.MI","c":"Settoriali SPDR","t":"STWX"},{"y":"STZX.MI","c":"Settoriali SPDR","t":"STZX"},
    {"y":"SWRD.MI","c":"Benchmark","t":"SWRD"},{"y":"600X.MI","c":"Benchmark","t":"600X"},
    {"y":"ADS.DE","c":"EUROGROW","t":"ADS"},{"y":"ADYEN.AS","c":"EUROGROW","t":"ADYEN"},
    {"y":"AI.PA","c":"EUROGROW","t":"AI"},{"y":"AIR.PA","c":"EUROGROW","t":"AIR"},
    {"y":"AM.PA","c":"EUROGROW","t":"AM"},{"y":"ASML.SW","c":"EUROGROW","t":"ASML"},
    {"y":"BEI.DE","c":"EUROGROW","t":"BEI"},{"y":"CBK.DE","c":"EUROGROW","t":"CBK"},
    {"y":"DB1.DE","c":"EUROGROW","t":"DB1"},{"y":"DSY.PA","c":"EUROGROW","t":"DSY"},
    {"y":"DTE.DE","c":"EUROGROW","t":"DTE"},{"y":"EL.PA","c":"EUROGROW","t":"EL"},
    {"y":"ENR.DE","c":"EUROGROW","t":"ENR"},{"y":"HEI.DE","c":"EUROGROW","t":"HEI"},
    {"y":"HO.PA","c":"EUROGROW","t":"HO"},{"y":"IFX.DE","c":"EUROGROW","t":"IFX"},
    {"y":"KNEBV.HE","c":"EUROGROW","t":"KNEBV"},{"y":"LDO.MI","c":"EUROGROW","t":"LDO"},
    {"y":"LR.PA","c":"EUROGROW","t":"LR"},{"y":"MC.PA","c":"EUROGROW","t":"MC"},
    {"y":"NOKIA.HE","c":"EUROGROW","t":"NOKIA"},{"y":"OR.PA","c":"EUROGROW","t":"OR"},
    {"y":"PRX.AS","c":"EUROGROW","t":"PRX"},{"y":"PRY.MI","c":"EUROGROW","t":"PRY"},
    {"y":"RACE.MI","c":"EUROGROW","t":"RACE"},{"y":"RHM.DE","c":"EUROGROW","t":"RHM"},
    {"y":"RMS.PA","c":"EUROGROW","t":"RMS"},{"y":"SAF.PA","c":"EUROGROW","t":"SAF"},
    {"y":"SAP.DE","c":"EUROGROW","t":"SAP"},{"y":"SHL.DE","c":"EUROGROW","t":"SHL"},
    {"y":"SIE.DE","c":"EUROGROW","t":"SIE"},{"y":"SRT.DE","c":"EUROGROW","t":"SRT"},
    {"y":"SU.PA","c":"EUROGROW","t":"SU"},{"y":"UCG.MI","c":"EUROGROW","t":"UCG"},
    {"y":"UMG.AS","c":"EUROGROW","t":"UMG"},{"y":"BAYN.F","c":"PORTAFOGLIO","t":"BAYN"},
]

# ── Fetch Yahoo ───────────────────────────────────────────────────────────────
def fetch_yahoo(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1y"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return data.get("chart", {}).get("result", [None])[0]
    except Exception as e:
        print(f"  ✗ {symbol}: {e}")
        return None

# ── Indicatori ────────────────────────────────────────────────────────────────
def ema_arr(arr, p):
    k = 2 / (p + 1)
    out = [arr[0]]
    for i in range(1, len(arr)):
        out.append(arr[i] * k + out[-1] * (1 - k))
    return out

def calc_kama(close, n=10, fast=2, slow=30):
    fast_sc, slow_sc = 2/(fast+1), 2/(slow+1)
    out = [None] * len(close)
    if len(close) < n + 1: return out
    out[n] = close[n]
    for i in range(n+1, len(close)):
        direction = abs(close[i] - close[i-n])
        noise = sum(abs(close[j] - close[j-1]) for j in range(i-n+1, i+1))
        er = direction / noise if noise else 0
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        out[i] = out[i-1] + sc * (close[i] - out[i-1])
    return out

def calc_sar(high, low, af_start=0.02, af_max=0.20):
    """Parabolic SAR — restituisce (sar_arr, trend_arr)
    trend: +1 = rialzo, -1 = ribasso"""
    n = len(high)
    sar = [0.0] * n
    trend = [1] * n
    ep = low[0]   # extreme point
    af = af_start
    sar[0] = high[0]

    for i in range(1, n):
        prev_sar = sar[i-1]
        prev_trend = trend[i-1]

        if prev_trend == 1:  # uptrend
            sar[i] = prev_sar + af * (ep - prev_sar)
            sar[i] = min(sar[i], low[i-1], low[i-2] if i >= 2 else low[i-1])
            if low[i] < sar[i]:  # inversione ribasso
                trend[i] = -1
                sar[i] = ep
                ep = low[i]
                af = af_start
            else:
                trend[i] = 1
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + af_start, af_max)
        else:  # downtrend
            sar[i] = prev_sar + af * (ep - prev_sar)
            sar[i] = max(sar[i], high[i-1], high[i-2] if i >= 2 else high[i-1])
            if high[i] > sar[i]:  # inversione rialzo
                trend[i] = 1
                sar[i] = ep
                ep = high[i]
                af = af_start
            else:
                trend[i] = -1
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + af_start, af_max)
    return sar, trend

def calc_ao(high, low):
    mid = [(h+l)/2 for h,l in zip(high, low)]
    e7 = ema_arr(mid, 7)
    e34 = ema_arr(mid, 34)
    return [a-b for a,b in zip(e7, e34)]

def calc_rsi(close, p=14):
    if len(close) < p + 1: return None
    gains = losses = 0
    for i in range(1, p+1):
        d = close[i] - close[i-1]
        if d >= 0: gains += d
        else: losses -= d
    ag, al = gains/p, losses/p
    for i in range(p+1, len(close)):
        d = close[i] - close[i-1]
        if d >= 0: ag = (ag*(p-1)+d)/p
        else: al = (al*(p-1)-d)/p
    return round(100 - 100/(1+ag/al), 1) if al else 100.0

def calc_er(close, n=10):
    if len(close) < n+1: return 0
    direction = abs(close[-1] - close[-1-n])
    noise = sum(abs(close[i]-close[i-1]) for i in range(len(close)-n, len(close)))
    return direction/noise if noise else 0

def trendycator(close):
    if len(close) < 55: return 'GRIGIO'
    e21 = ema_arr(close, 21)
    e55 = ema_arr(close, 55)
    if e21[-1] > e55[-1] and e21[-1] > e21[-2]: return 'VERDE'
    if e21[-1] < e55[-1] and e21[-1] < e21[-2]: return 'ROSSO'
    return 'GRIGIO'

def calc_baffetti(ao):
    b = 0
    for i in range(len(ao)-1, 0, -1):
        if ao[i] > ao[i-1]: b += 1
        else: break
    return b

def sma(arr, p):
    if len(arr) < p: return None
    return sum(arr[-p:]) / p

def vol_ratio(volume):
    if len(volume) < 21: return 1.0
    avg20 = sum(volume[-21:-1]) / 20
    return round(volume[-1]/avg20, 2) if avg20 else 1.0

def cross_days(close, kama):
    for i in range(len(close)-1, 0, -1):
        if kama[i] is not None and kama[i-1] is not None:
            if close[i] > kama[i] and close[i-1] <= kama[i-1]:
                return len(close)-1-i
    return 999

# ── Analisi singolo ticker ────────────────────────────────────────────────────
def analyze(info):
    base = {"ticker": info["t"], "display": info["t"], "categoria": info["c"],
            "error": None, "score": 0, "tipo": "", "uscita": ""}
    raw = fetch_yahoo(info["y"])
    if not raw:
        return {**base, "error": "fetch failed"}
    try:
        q = raw["indicators"]["quote"][0]
        ts_raw = raw["timestamp"]
        closes_r = q["close"]; highs_r = q["high"]
        lows_r   = q["low"];   vols_r  = q["volume"]

        c, h, l, v, t = [], [], [], [], []
        for i in range(len(ts_raw)):
            if closes_r[i] and highs_r[i] and lows_r[i]:
                c.append(closes_r[i]); h.append(highs_r[i]); l.append(lows_r[i])
                v.append(vols_r[i] or 0); t.append(ts_raw[i])
        if len(c) < 60:
            return {**base, "error": "Dati insuff."}

        # ── Indicatori ──
        kama_v  = calc_kama(c, n=5,  fast=2, slow=10)   # veloce → entrata
        kama_s  = calc_kama(c, n=21, fast=2, slow=30)   # lenta  → stop base
        sar, sar_trend = calc_sar(h, l)
        ao      = calc_ao(h, l)
        baff    = calc_baffetti(ao)
        er      = calc_er(c)
        trd     = trendycator(c)
        rsi     = calc_rsi(c)
        mm20    = sma(c, 20)
        mm50    = sma(c, 50)
        mm200   = sma(c, 200)

        price      = c[-1]
        kv_now     = kama_v[-1]
        ks_now     = kama_s[-1]
        sar_now    = sar[-1]
        sar_up     = sar_trend[-1] == 1
        ao_now     = ao[-1]
        above_kv   = kv_now is not None and price > kv_now
        above_ks   = ks_now is not None and price > ks_now
        mm_align   = bool(mm20 and mm50 and price > mm20 and mm20 > mm50)
        cross      = cross_days(c, kama_v)
        perf_sett  = round((price/c[-6]-1)*100, 2)  if len(c) >= 6  else 0
        perf_mese  = round((price/c[-23]-1)*100, 2) if len(c) >= 23 else 0
        pk_pct_v   = round((price - kv_now) / kv_now * 100, 2) if kv_now else 0
        vr         = vol_ratio(v)

        # ── Segnale ──
        tipo = ""
        if trd == 'VERDE' and above_kv and sar_up and er >= 0.45 and baff >= 3 and mm_align:
            tipo = 'LONG'
        elif above_kv and sar_up and baff >= 3 and trd in ('VERDE','GRIGIO'):
            tipo = 'EARLY'
        elif above_kv and baff >= 1 and trd in ('VERDE','GRIGIO'):
            tipo = 'WATCH'
        elif trd == 'ROSSO' and cross <= 3 and baff >= 3:
            tipo = 'ROSSO+'

        # ── Uscita ──
        uscita = ""
        if not above_kv and trd == 'ROSSO': uscita = 'STOP'
        elif not above_kv:                   uscita = 'USCITA'
        elif above_kv and (ao_now <= 0 or trd == 'GRIGIO'): uscita = 'ATTENZIONE'

        # ── Prezzi entrata / stop / target ──
        stop_price   = round(max(sar_now, ks_now if ks_now else sar_now), 4)
        entry_price  = round(price, 4)
        risk         = entry_price - stop_price
        target_price = round(entry_price + risk * 2, 4) if risk > 0 else None
        risk_pct     = round(-risk / entry_price * 100, 2) if risk > 0 else 0
        reward_pct   = round(risk * 2 / entry_price * 100, 2) if risk > 0 else 0

        # ── Motivazione segnale ──
        reasons = []
        checks  = {}
        checks["Trendycator VERDE"]   = trd == 'VERDE'
        checks["Prezzo > KAMA veloce"] = above_kv
        checks["Prezzo > KAMA lenta"]  = above_ks
        checks["SAR rialzista"]        = sar_up
        checks["ER ≥ 0.45"]            = er >= 0.45
        checks["Baffetti ≥ 3"]         = baff >= 3
        checks["MM allineate"]         = mm_align
        checks["AO positivo"]          = ao_now > 0
        checks["RSI > 50"]             = rsi is not None and rsi > 50
        for k, v2 in checks.items():
            reasons.append({"label": k, "ok": v2})

        # ── Score ──
        score = (er*30 + min(baff,10)*5 + min(abs(pk_pct_v),5)*3
                 + max(-10,min(5,perf_sett))*4
                 + max(-20,min(10,perf_mese))*2
                 + (10 if mm_align else 0)
                 + (5  if ao_now > 0 else 0)
                 + (5  if sar_up else 0)
                 + (20 if cross<=3 else 12 if cross<=10 else 5 if cross<=20 else 0))
        if trd == 'ROSSO': score *= 0.6
        score = int(max(0, min(200, round(score))))

        return {
            "ticker": info["t"], "display": info["t"], "categoria": info["c"],
            "price":       entry_price,
            "kama_v":      round(kv_now, 4) if kv_now else None,
            "kama_s":      round(ks_now, 4) if ks_now else None,
            "sar":         round(sar_now, 4),
            "sar_up":      sar_up,
            "er":          round(er, 3),
            "baff":        baff,
            "trendycator": trd,
            "rsi":         rsi,
            "mm20":        round(mm20, 4) if mm20 else None,
            "mm50":        round(mm50, 4) if mm50 else None,
            "mm200":       round(mm200, 4) if mm200 else None,
            "mm_align":    mm_align,
            "ao_pos":      ao_now > 0,
            "pk_pct":      pk_pct_v,
            "perf_sett":   perf_sett,
            "perf_mese":   perf_mese,
            "vol_ratio":   vr,
            "score":       score,
            "tipo":        tipo,
            "uscita":      uscita,
            "cross":       cross,
            # Prezzi operativi
            "entry_price":  entry_price,
            "entry_date":   NOW_DATE,
            "entry_time":   NOW_TIME,
            "stop_price":   stop_price,
            "target_price": target_price,
            "risk_pct":     risk_pct,
            "reward_pct":   reward_pct,
            # Motivazione
            "reasons":     reasons,
            "error":       None
        }
    except Exception as e:
        return {**base, "error": str(e)}

# ── Storico segnali ───────────────────────────────────────────────────────────
def load_history():
    try:
        with open("data/history.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_history(history):
    os.makedirs("data", exist_ok=True)
    with open("data/history.json", "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def update_history(results, history):
    """Aggiorna storico e restituisce le novità"""
    news = {"new_long":[], "new_early":[], "new_watch":[],
            "new_rosso":[], "new_stop":[], "new_exit":[], "new_att":[]}

    for r in results:
        if r.get("error") and not r.get("price"): continue
        tk   = r["ticker"]
        tipo = r.get("tipo","")
        usc  = r.get("uscita","")
        prev = history.get(tk, {})
        prev_tipo = prev.get("tipo","")
        prev_usc  = prev.get("uscita","")

        # Nuovi segnali
        if tipo != prev_tipo:
            entry = {
                "ticker":       tk,
                "categoria":    r["categoria"],
                "tipo":         tipo,
                "entry_price":  r.get("entry_price"),
                "entry_date":   NOW_DATE,
                "entry_time":   NOW_TIME,
                "stop_price":   r.get("stop_price"),
                "target_price": r.get("target_price"),
                "risk_pct":     r.get("risk_pct"),
                "reward_pct":   r.get("reward_pct"),
                "score":        r.get("score"),
            }
            if tipo == "LONG":   news["new_long"].append(entry)
            if tipo == "EARLY":  news["new_early"].append(entry)
            if tipo == "WATCH":  news["new_watch"].append(entry)
            if tipo == "ROSSO+": news["new_rosso"].append(entry)

        # Nuove uscite
        if usc != prev_usc:
            exit_entry = {
                "ticker":      tk,
                "categoria":   r["categoria"],
                "uscita":      usc,
                "exit_price":  r.get("price"),
                "exit_date":   NOW_DATE,
                "exit_time":   NOW_TIME,
                "entry_price": prev.get("entry_price"),
                "entry_date":  prev.get("entry_date","—"),
                "entry_time":  prev.get("entry_time","—"),
                "result_pct":  round((r["price"] - prev["entry_price"]) / prev["entry_price"] * 100, 2)
                               if prev.get("entry_price") else None,
            }
            if usc == "STOP":       news["new_stop"].append(exit_entry)
            if usc == "USCITA":     news["new_exit"].append(exit_entry)
            if usc == "ATTENZIONE": news["new_att"].append(exit_entry)

        # Aggiorna storico
        history[tk] = {
            "tipo":        tipo,
            "uscita":      usc,
            "entry_price": r.get("entry_price") if tipo and not prev_tipo else prev.get("entry_price"),
            "entry_date":  NOW_DATE if tipo and not prev_tipo else prev.get("entry_date","—"),
            "entry_time":  NOW_TIME if tipo and not prev_tipo else prev.get("entry_time","—"),
            "stop_price":  r.get("stop_price"),
            "target_price":r.get("target_price"),
        }

    return news

# ── Mail ──────────────────────────────────────────────────────────────────────
def fmt_entry(e):
    res = f"  • {e['ticker']} ({e['categoria']})  score {e.get('score','—')}\n"
    res += f"    Entrata:  {e['entry_date']} {e['entry_time']}  prezzo {e.get('entry_price','—')}\n"
    res += f"    Stop:     {e.get('stop_price','—')}  ({e.get('risk_pct','—')}%)\n"
    res += f"    Target:   {e.get('target_price','—')}  (+{e.get('reward_pct','—')}%)\n"
    return res

def fmt_exit(e):
    res = f"  • {e['ticker']} ({e['categoria']})\n"
    res += f"    Uscita:   {e['exit_date']} {e['exit_time']}  prezzo {e.get('exit_price','—')}\n"
    if e.get("entry_price"):
        res += f"    Entrato:  {e['entry_date']} {e['entry_time']}  prezzo {e['entry_price']}\n"
    if e.get("result_pct") is not None:
        sign = "+" if e["result_pct"] >= 0 else ""
        res += f"    Risultato: {sign}{e['result_pct']}%\n"
    return res

def send_mail(news):
    has_news = any(news[k] for k in news)
    if not has_news:
        print("  ✉ Nessuna novità — mail non inviata")
        return
    if not GMAIL_USER or not GMAIL_PASSWORD or not MAIL_TO:
        print("  ✉ Credenziali mail non configurate — skip")
        return

    body = f"🦅 RAPTOR Alert — Aggiornamento {NOW}\n"
    body += "=" * 50 + "\n\n"

    if news["new_long"]:
        body += f"🟢 NUOVI LONG ({len(news['new_long'])})\n"
        for e in news["new_long"]: body += fmt_entry(e)
        body += "\n"
    if news["new_early"]:
        body += f"🔵 NUOVI EARLY ({len(news['new_early'])})\n"
        for e in news["new_early"]: body += fmt_entry(e)
        body += "\n"
    if news["new_watch"]:
        body += f"🟡 NUOVI WATCH ({len(news['new_watch'])})\n"
        for e in news["new_watch"]: body += fmt_entry(e)
        body += "\n"
    if news["new_rosso"]:
        body += f"🔴 NUOVI ROSSO+ ({len(news['new_rosso'])})\n"
        for e in news["new_rosso"]: body += fmt_entry(e)
        body += "\n"
    if news["new_stop"]:
        body += f"⛔ NUOVI STOP ({len(news['new_stop'])})\n"
        for e in news["new_stop"]: body += fmt_exit(e)
        body += "\n"
    if news["new_exit"]:
        body += f"🔴 NUOVE USCITE ({len(news['new_exit'])})\n"
        for e in news["new_exit"]: body += fmt_exit(e)
        body += "\n"
    if news["new_att"]:
        body += f"🟡 NUOVE ATTENZIONI ({len(news['new_att'])})\n"
        for e in news["new_att"]: body += fmt_exit(e)
        body += "\n"

    body += f"\nVedi tutti i dati: https://giorgiogoldoni.github.io/raptor-alert/\n"

    msg = MIMEMultipart()
    msg["From"]    = GMAIL_USER
    msg["To"]      = MAIL_TO
    msg["Subject"] = f"🦅 RAPTOR Alert {NOW} — {sum(len(news[k]) for k in news)} novità"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_PASSWORD)
            s.send_message(msg)
        print(f"  ✉ Mail inviata a {MAIL_TO}")
    except Exception as e:
        print(f"  ✉ Errore mail: {e}")

# ── Stats / contatore ─────────────────────────────────────────────────────────
def update_stats(ok, errors):
    os.makedirs("data", exist_ok=True)
    try:
        with open("data/stats.json", "r") as f:
            stats = json.load(f)
    except:
        stats = {"run_count_mese": 0, "run_count_totale": 0,
                 "minuti_stimati_mese": 0, "reset_mese": NOW_DATE[:5]}

    # reset mensile
    current_month = NOW_DATE[3:5]
    if stats.get("reset_mese","") != NOW_DATE[3:5]:
        stats["run_count_mese"]      = 0
        stats["minuti_stimati_mese"] = 0
        stats["reset_mese"]          = current_month

    stats["run_count_mese"]       += 1
    stats["run_count_totale"]     += 1
    stats["minuti_stimati_mese"]  += 3
    stats["ultimo_run"]            = NOW
    stats["ultimo_ok"]             = ok
    stats["ultimo_errori"]         = errors

    with open("data/stats.json", "w") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"  📊 Run mese: {stats['run_count_mese']} · Minuti stimati: {stats['minuti_stimati_mese']}/2000")
    return stats

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"🦅 RAPTOR Alert v2.0 — {NOW}")
    print(f"   Ticker da analizzare: {len(TICKERS)}")

    results = []
    ok = err = 0
    for i, ticker in enumerate(TICKERS):
        print(f"  [{i+1:3}/{len(TICKERS)}] {ticker['t']:<12}", end=" ", flush=True)
        r = analyze(ticker)
        results.append(r)
        if r["error"]:
            print(f"✗ {r['error']}")
            err += 1
        else:
            print(f"✓ {r.get('tipo','—'):6} score={r.get('score',0):3}  "
                  f"entrata={r.get('entry_price','?')}  "
                  f"stop={r.get('stop_price','?')}  "
                  f"target={r.get('target_price','?')}")
            ok += 1
        time.sleep(0.3)

    # Storico e novità
    print("\n📋 Aggiornamento storico...")
    history = load_history()
    news    = update_history(results, history)
    save_history(history)

    total_news = sum(len(news[k]) for k in news)
    print(f"   Novità trovate: {total_news}")

    # Mail
    print("\n✉ Invio mail...")
    send_mail(news)

    # Salva JSON dati
    os.makedirs("data", exist_ok=True)
    output = {
        "updated":      NOW,
        "updated_date": NOW_DATE,
        "updated_time": NOW_TIME,
        "total":        len(results),
        "ok":           ok,
        "errors":       err,
        "data":         results
    }
    with open("data/etf.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(',',':'))

    # Stats
    stats = update_stats(ok, err)

    print(f"\n✅ Completato: {ok} ok · {err} errori")
    print(f"   JSON: data/etf.json ({len(results)} ETF)")
    print(f"   Run mese: {stats['run_count_mese']} · ~{stats['minuti_stimati_mese']} min usati")

if __name__ == "__main__":
    main()
