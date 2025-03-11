#/bin/bash

uv run ./partition_latest.py /data/ssd2/streamflow-ml-data-operational/operational-output/current_partition
rsync -ravz /data/ssd2/streamflow-ml-data-operational/operational-output/current_partition/ data.climate.umt.edu:/var/data/hhp/current