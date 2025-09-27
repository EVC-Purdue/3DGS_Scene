cd /workspace/3DGS_Scene
pip install cv2

mkdir ~/.aws
touch ~/.aws/config
cat > "$HOME/.aws/config" << EOL
[default]
aws_access_key_id = $AWS_ACCESS_KEY
aws_secret_access_key = $AWS_SECRET_ACCESS_KEY
EOL

mkdir data
mkdir videos
s5cmd cp s3://purdue-evc-data/photos/* ./data/
s5cmd cp s3://purdue-evc-data/videos/* ./videos/

python runner.py