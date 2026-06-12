.ONESHELL:

INSTALL_DIR  = /usr/libexec/pipeline
DATA_DIR     = /usr/share/pipeline
SERVICE_FILE = /etc/systemd/system/pipeline.service

.PHONY: install uninstall

install:
	groupadd -r pipeline || true
	useradd -r -g pipeline -M -s /usr/sbin/nologin pipeline || true
	usermod -aG docker pipeline
	install -d $(INSTALL_DIR)
	cp -r pipeline start-pipeline $(INSTALL_DIR)/
	chmod +x $(INSTALL_DIR)/start-pipeline
	install -d -o pipeline -g pipeline $(DATA_DIR)
	cat > $(SERVICE_FILE) <<-EOF
	[Unit]
	Description=Pipeline automation server
	After=network.target docker.service
	Wants=docker.service

	[Service]
	Type=simple
	User=pipeline
	Group=pipeline
	ExecStart=$(INSTALL_DIR)/start-pipeline --data $(DATA_DIR)
	Restart=on-failure
	RestartSec=5

	[Install]
	WantedBy=multi-user.target
	EOF
	systemctl daemon-reload
	systemctl enable pipeline

uninstall:
	systemctl disable --now pipeline || true
	rm -f $(SERVICE_FILE)
	systemctl daemon-reload
	rm -rf $(INSTALL_DIR)
	userdel pipeline || true
	groupdel pipeline || true
