FROM checkio/cli_interface:0.1

RUN mkdir /opt/balance

RUN wget https://raw.githubusercontent.com/CheckiO/eoc-balance/master/balance.json -O /opt/balance/balance.json
RUN wget https://raw.githubusercontent.com/CheckiO/eoc-balance/master/private_balance.json -O /opt/balance/private_balance.json

COPY ./requirements.txt /root/requirements.txt
RUN pip install -r /root/requirements.txt
