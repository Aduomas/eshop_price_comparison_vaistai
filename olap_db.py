import pyodbc
import pandas as pd
import warnings
from datetime import datetime
from configparser import ConfigParser

warnings.filterwarnings("ignore")


def fetch_dataframe():
    config = ConfigParser()
    config.read("config.ini")
    db_param = config["database"]

    conn = pyodbc.connect(
        f"DRIVER={db_param['DRIVER']};SERVER={db_param['SERVER']};DATABASE={db_param['DATABASE']};Trusted_Connection={db_param['Trusted_Connection']};UID={db_param['UID']};PWD={db_param['PWD']};"
    )

    last_year_date = (
        datetime.now()
        .replace(year=datetime.now().year - 1, month=1, day=1)
        .strftime("%Y/%m/%d")
    )
    this_year_date = datetime.now().replace(month=1, day=1).strftime("%Y/%m/%d")
    now = datetime.now().strftime("%Y/%m/%d")

    sql_query = f"""
    SELECT dbo.Prekes_SK.Pavad,
            dbo.Prekes_SK.Kodas,
            Sum(case when dbo.OperacijuTipai_SK.OperacijuTipaiId IN (50, 45, 61, 67, 68) then dbo.OpPozicijosPard_SK.Kiekis else 0 end)
            - Sum(case when dbo.OperacijuTipai_SK.OperacijuTipaiId IN (64, 73) then dbo.OpPozicijosPard_SK.Kiekis else 0 end) AS Kiekis,
            Sum(case when dbo.OperacijuTipai_SK.OperacijuTipaiId IN (50, 45, 61, 67, 68) then Kiekis * KainaPoNuolaidosBePVM else 0 end)
            - Sum(case when dbo.OperacijuTipai_SK.OperacijuTipaiId IN (64, 73) then Kiekis * KainaPoNuolaidosBePVM else 0 end) AS BePVM,
            dbo.Prekes_SK.PrekesId
      FROM dbo.Partneriai_SK INNER JOIN (dbo.OperacijuTipai_SK INNER JOIN ((dbo.OpPozicijosPard_SK INNER JOIN dbo.Prekes_SK ON dbo.OpPozicijosPard_SK.PrekesId = dbo.Prekes_SK.PrekesId) INNER JOIN dbo.OperacijosPard_SK ON dbo.OpPozicijosPard_SK.OperacijosId = dbo.OperacijosPard_SK.OperacijosId) ON dbo.OperacijuTipai_SK.OperacijuTipaiId = dbo.OperacijosPard_SK.OperacijuTipaiId) ON dbo.Partneriai_SK.PartneriaiId = dbo.OperacijosPard_SK.PartneriaiId
      WHERE (dbo.OperacijosPard_SK.Data Between '{this_year_date}' And '{now}')
      GROUP BY dbo.Prekes_SK.Pavad, dbo.Prekes_SK.PrekesId, dbo.Prekes_SK.Kodas
      ORDER BY BePVM DESC;

    """

    df = pd.read_sql(sql_query, conn)
    conn.close()
    return df
