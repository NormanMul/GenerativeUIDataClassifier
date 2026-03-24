#!/usr/bin/env bash
# Generate Python gRPC stubs from proto definitions
set -euo pipefail

PROTO_DIR="shared/proto"
OUT_DIR="src/shared_grpc"

mkdir -p "$OUT_DIR"

python -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUT_DIR" \
    --grpc_python_out="$OUT_DIR" \
    --pyi_out="$OUT_DIR" \
    "$PROTO_DIR"/*.proto

# Fix imports in generated files
find "$OUT_DIR" -name "*.py" -exec sed -i 's/^import \(.*\)_pb2/from . import \1_pb2/' {} +

echo "gRPC stubs generated in $OUT_DIR"
