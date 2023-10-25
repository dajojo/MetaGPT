# Use a base image with Python3.9 and Nodejs20 slim version
FROM nikolaik/python-nodejs:python3.9-nodejs20-slim

# Install Debian software needed by MetaGPT and clean up in one RUN command to reduce image size
RUN apt update &&\
    apt install -y git chromium fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 --no-install-recommends &&\
    apt clean && rm -rf /var/lib/apt/lists/*

# Install Mermaid CLI globally
ENV CHROME_BIN="/usr/bin/chromium" \
    PUPPETEER_CONFIG="/app/metagpt/config/puppeteer-config.json"\
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD="true"
RUN npm install -g @mermaid-js/mermaid-cli &&\
    npm cache clean --force

# Install Python dependencies and install MetaGPT
COPY . /app/metagpt
WORKDIR /app/metagpt
RUN mkdir workspace &&\
    pip install --no-cache-dir -r requirements.txt &&\
    pip install -e.

# Running with an infinite loop using the tail command
CMD ["sh", "-c", "tail -f /dev/null"]


# # Use a base image with Python3.9 and Nodejs20 slim version
# FROM nikolaik/python-nodejs:python3.9-nodejs20-slim

# # Install Debian software needed by MetaGPT and clean up in one RUN command to reduce image size
# RUN apt update &&\
#     apt install -y git chromium fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 unzip xz-utils curl --no-install-recommends &&\
#     apt clean && rm -rf /var/lib/apt/lists/*

# # Install Mermaid CLI globally
# ENV CHROME_BIN="/usr/bin/chromium" \
#     PUPPETEER_CONFIG="/app/metagpt/config/puppeteer-config.json"\
#     PUPPETEER_SKIP_CHROMIUM_DOWNLOAD="true"
# RUN npm install -g @mermaid-js/mermaid-cli &&\
#     npm cache clean --force

# # Install Flutter
# ENV FLUTTER_HOME="/opt/flutter"
# RUN cd /tmp &&\
#     curl -O https://storage.googleapis.com/flutter_infra/releases/stable/linux/flutter_linux_2.8.1-stable.tar.xz &&\
#     tar xf flutter_linux_2.8.1-stable.tar.xz -C /opt &&\
#     rm flutter_linux_2.8.1-stable.tar.xz
# ENV PATH="$PATH:$FLUTTER_HOME/bin"

# # Install Python dependencies and install MetaGPT
# COPY . /app/metagpt
# WORKDIR /app/metagpt
# RUN mkdir workspace &&\
#     pip install --no-cache-dir -r requirements.txt &&\
#     pip install -e.

# # Running with an infinite loop using the tail command
# CMD ["sh", "-c", "tail -f /dev/null"]