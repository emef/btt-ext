pushd `dirname $0` > /dev/null
DEPLOYDIR=`pwd`
popd > /dev/null
TMPFILESCONF=$DEPLOYDIR/tmpfiles.conf
SERVICECONF=$DEPLOYDIR/buythistweet.service
NGINXCONF=$DEPLOYDIR/nginx.conf
APPDIR=`realpath $DEPLOYDIR/../server/`
EXTDIR=`realpath $DEPLOYDIR/../extension/`

deploy() {
    set -e

    if [ -z "$BTT_HOST" ]; then
        echo "missing host environment variable \$BTT_HOST"
        echo "    - should be set to \$user@\$host"
        exit 1
    fi

    echo "deploying to $BTT_HOST"
    echo "assumed dependencies on server:"
    echo "    - ubuntu server"
    echo "    - user buythistweet exists"
    echo "    - nginx installed"
    echo "    - virtualenv installed"
    echo "    - Google Chrome installed at /usr/bin/google-chrome"
    echo "    - PIL dependencies: libjpeg-dev libpng-dev zlib1g-dev"

    echo "uploading app code"
    ssh $BTT_HOST "mkdir -p ./buythistweet"
    ssh $BTT_HOST "rm -rf ./buythistweet/*"
    rsync -az --exclude node_modules $APPDIR $BTT_HOST:./buythistweet/
    ssh $BTT_HOST "sudo mkdir -p /opt/buythistweet/server"
    ssh $BTT_HOST "sudo rm -rf /opt/buythistweet/server/*"
    ssh $BTT_HOST "sudo mv buythistweet/server/* /opt/buythistweet/server/"
    ssh $BTT_HOST "rm -rf ./buythistweet"
    ssh $BTT_HOST "sudo chown -R buythistweet /opt/buythistweet"

    echo "setting up virtualenv"
    ssh $BTT_HOST "sudo mkdir -p /opt/virtualenv"
    ssh $BTT_HOST "sudo virtualenv /opt/virtualenv/buythistweet || echo -n" &>/dev/null
    ssh $BTT_HOST "sudo /opt/virtualenv/buythistweet/bin/pip install -r /opt/buythistweet/server/requirements.txt" &>/dev/null

    echo "stopping server for deploy"
    ssh $BTT_HOST "sudo systemctl stop buythistweet.service || echo -n" &>/dev/null

    echo "installing tmpfiles config"
    scp $TMPFILESCONF $BTT_HOST: &>/dev/null
    ssh $BTT_HOST "sudo mv tmpfiles.conf /etc/tmpfiles.d/"
    ssh $BTT_HOST "sudo systemd-tmpfiles --create" &>/dev/null

    echo "installing systemd service"
    scp $SERVICECONF $BTT_HOST: &>/dev/null
    ssh $BTT_HOST "sudo mv buythistweet.service /lib/systemd/system/"
    ssh $BTT_HOST "sudo chmod 755 /lib/systemd/system/buythistweet.service"
    ssh $BTT_HOST "sudo systemctl enable buythistweet.service"

    echo "installing nginx config and restarting it"
    scp $NGINXCONF $BTT_HOST: &>/dev/null
    ssh $BTT_HOST "sudo rm -f /etc/nginx/sites-enabled/default"
    ssh $BTT_HOST "sudo mv nginx.conf /etc/nginx/sites-available/buythistweet"
    ssh $BTT_HOST "sudo ln -s /etc/nginx/sites-available/buythistweet /etc/nginx/sites-enabled/ || echo -n" &>/dev/null

    echo "restarting services"
    ssh $BTT_HOST "sudo systemctl daemon-reload"
    ssh $BTT_HOST "sudo systemctl start buythistweet.service"
    ssh $BTT_HOST "sudo service nginx restart"

    echo "deploy success"
}

deploy
