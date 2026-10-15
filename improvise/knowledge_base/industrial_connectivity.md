# Industrial connectivity - choosing a protocol

- OPC UA: vendor-neutral, structured data with types and browsing, built-in security
  (certificates, encryption). First choice for connecting PLCs and machines to MES/SCADA/IT
  when the controller supports it. Python: asyncua.
- MQTT: lightweight publish/subscribe through a broker. Good for many devices sending data to
  dashboards and cloud; needs a topic convention (site/area/line/machine/signal) and a payload
  format (e.g. JSON with value and timestamp). Use TLS and per-device credentials. Python: paho-mqtt.
- Modbus TCP/RTU: simple register/coil reads, very common on drives, meters and small
  controllers; no data types or security of its own - keep it on an isolated network. Python: pymodbus.
- Siemens S7 (ISO-on-TCP): direct read of data blocks on S7 PLCs where OPC UA is not available.
  Python: python-snap7. Optimised blocks may need to be made accessible in the project.
- EtherNet/IP (CIP): Allen-Bradley / Rockwell controllers. Python: pycomm3.
- Beckhoff ADS: TwinCAT controllers. Python: pyads.

Rules for data collection from machines:
- Read-only by default; writing setpoints or commands to a controller is a separate, approved design.
- Put a gateway between the control network and the office network; never expose PLCs to the internet.
- Collect at least: running state, fault/alarm code, good count, reject count, current recipe/product.
- Timestamp at the source when possible; buffer data at the edge during network outages.
