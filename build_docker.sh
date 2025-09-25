#!/usr/bin/env bash


# git submodule update --init --recursive
# docker build -t acbotics/acsense:$(arch) .

if [[ ! $(docker buildx ls | grep multi-platform-builder ) ]]; then

    docker buildx create \
        --use --platform=linux/arm64,linux/amd64,linux/arm/v8,linux/arm/v7,linux/arm/v6 \
        --name multi-platform-builder \
        --config /etc/buildkit/buildkitd.toml \
        --bootstrap
    # docker buildx inspect --bootstrap

fi


docker run --rm --privileged multiarch/qemu-user-static:register --reset 2&> /dev/null
sleep 1

    # --platform linux/amd64,linux/arm64,linux/arm/v8,linux/arm/v7  \
docker buildx build \
    --platform linux/amd64,linux/arm64  \
    --output type=local,dest=dist/dist_ubuntu2404 \
    --file docker/ubuntu2404.dockerfile \
    .

# docker buildx build \
#     --platform linux/amd64,linux/arm64  \
#     --output type=local,dest=dist/dist_ubuntu2204 \
#     --file docker/ubuntu2204.dockerfile \
#     .

docker buildx build \
    --platform linux/amd64,linux/arm64,linux/arm/v8  \
    --output type=local,dest=dist/dist_debian_bookworm \
    --file docker/debian_bookworm.dockerfile \
    .

echo "Done"
