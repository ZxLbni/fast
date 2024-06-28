FROM hrishi2861/terabox:latest
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["bash", "start.sh"]
