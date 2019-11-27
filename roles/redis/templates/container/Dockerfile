FROM redis:5.0.7-alpine

RUN echo "unixsocket /var/run/redis/redis.sock" >> /etc/redis.conf \
  && echo "unixsocketperm 666" >> /etc/redis.conf
  
ENTRYPOINT ["docker-entrypoint.sh"]

CMD [ "redis-server", "/etc/redis.conf" ]
