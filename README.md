# ImageExporter 🐳

A specialized tool for offline Docker image management and deployment. 🚢

## Supported Software 📦

<table style="border-collapse: collapse; width: 100%;">
  <thead>
    <tr style="background-color:rgb(242, 242, 242);">
      <th style="text-align: left; padding: 8px; vertical-align: middle;">Software</th>
      <th style="text-align: left; padding: 8px; vertical-align: middle;">Image Name</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">Elasticsearch </td>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">docker.io/library/elasticsearch</td>
    </tr>
    <tr>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">Nginx </td>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">docker.io/library/nginx</td>
    </tr>
    <tr>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">Redis </td>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">docker.io/library/redis</td>
    </tr>
    <tr>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">RabbitMQ </td>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">docker.io/library/rabbitmq</td>
    </tr>
    <tr>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">MinIO </td>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">docker.io/minio/minio</td>
    </tr>
    <tr>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">Nacos </td>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">docker.io/nacos/nacos-server</td>
    </tr>
    <tr>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">GeoServer </td>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">docker.io/kartoza/geoserver</td>
    </tr>
    <tr>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">PostgreSQL-PostGIS </td>
      <td style="text-align: left; padding: 8px; vertical-align: middle;">docker.io/freelabspace/postgresql-postgis</td>
    </tr>
  </tbody>
</table>



## Structure 🗂️

```
ImageExporter/
├── data/
│   ├── versions/     # Version info (e.g., latest-YYYYMMDD.txt, update-YYYYMMDD.txt) 📋
│   └── images/       # Exported images 🗃️
├── logs/             # Log files 📜
├── main.py           # Main script 🚀
```

## Usage 🛠️

1. Place historical version files in `data/versions` (optional, e.g., `latest-YYYYMMDD.txt`). 📥
2. Run the tool to check for updates and export images:

```bash
python main.py      # Normal mode 🌟
python main.py -D   # Debug mode 🐞
```

3. Check the generated version files (`latest-YYYYMMDD.txt` for all versions, `update-YYYYMMDD.txt` for updates needed) in `data/versions`. 🔍

## Cleanup 🧹

```bash
python main.py --clean      # Clean Python cache files 🗑️
python main.py --clean-all  # Clean all temporary files (cache, images, logs, today's versions) 🗑️🔥
```