cd /workspace/3DGS_Scene/src
rm -f colmap.db

while IFS= read -r d; do
  bn="$(basename "$d")"
  m="masks/$bn"

  if [ ! -d "$m" ]; then
    echo "WARNING: missing masks for $bn at $m — skipping"
    continue
  fi

  echo ">> Extracting: $d  (masks: $m)"
  colmap feature_extractor \
    --database_path colmap.db \
    --image_path "$d" \
    --ImageReader.mask_path "$m" \
    --ImageReader.camera_model OPENCV \
    --ImageReader.single_camera 1 \
    --SiftExtraction.use_gpu 1 \
    --SiftExtraction.max_num_features 20000

done < <(find video_frames -mindepth 1 -maxdepth 1 -type d -print)

colmap sequential_matcher \
  --database_path colmap.db \
  --SiftMatching.use_gpu 1 \
  --SiftMatching.guided_matching 1 \
  --SequentialMatching.overlap 15 \
  --SequentialMatching.loop_detection 1

# Spatial neighbor tightening
colmap spatial_matcher \
  --database_path colmap.db \
  --SiftMatching.use_gpu 1 \
  --SiftMatching.guided_matching 1

# Incremental mapping
mkdir -p colmap_sparse colmap_dense
colmap mapper \
  --database_path colmap.db \
  --image_path video_frames \
  --output_path colmap_sparse \
  --Mapper.multiple_models 0

# Undistort
colmap image_undistorter \
  --image_path video_frames \
  --input_path colmap_sparse/0 \
  --output_path colmap_dense \
  --output_type COLMAP

# Give to Nerfstudio
ns-process-data colmap \
  --colmap-model-path ./colmap_dense \
  --image-dir ./colmap_dense/images \
  --output-dir ./nerf_outdoor \
  --copy-images