
Run the following command to download census tracts

```bash
mkdir -p /home/kavi/temp/census_downloaded/
census-downloader --output /home/kavi/temp/census_downloaded/usa.csv --columns INTPTLAT INTPTLON POP100 SUMLEV --filter-level 140
```

Use this command to process them into a shapefile

```bash
python process.py
```