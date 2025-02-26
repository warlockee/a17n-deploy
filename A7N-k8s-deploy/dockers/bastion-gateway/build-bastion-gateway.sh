#!/bin/bash
# Script to build bastion-gateway Docker image
# Default is to build for AMD64 (x86_64) architecture

# Default values
IMAGE_NAME="bastion-gateway"
TAG="latest"
PLATFORM="amd64"  # Default to AMD64
BUILD_MULTI=false

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Display usage instructions
function show_help {
    echo -e "${GREEN}Bastion Gateway Docker Build Script${NC}"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -p, --platform PLATFORM    Build for specified platform (amd64, arm64)"
    echo "  -t, --tag TAG              Set image tag (default: latest)"
    echo "  -m, --multi                Build multi-architecture image (requires Docker buildx)"
    echo ""
    echo "Examples:"
    echo "  $0                         # Build for AMD64 (x86_64) with default tag"
    echo "  $0 -p arm64                # Build for ARM64 architecture"
    echo "  $0 -t v1.0                 # Build with custom tag v1.0"
    echo "  $0 -m                      # Build for multiple architectures using buildx"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift
            shift
            ;;
        -t|--tag)
            TAG="$2"
            shift
            shift
            ;;
        -m|--multi)
            BUILD_MULTI=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Validate platform
if [[ "$PLATFORM" != "amd64" && "$PLATFORM" != "arm64" && "$BUILD_MULTI" == "false" ]]; then
    echo -e "${RED}Error: Platform must be amd64 or arm64${NC}"
    exit 1
fi

# Display build configuration
echo -e "${GREEN}Building bastion-gateway Docker image${NC}"
echo -e "Image name: ${YELLOW}${IMAGE_NAME}:${TAG}${NC}"

if [ "$BUILD_MULTI" = true ]; then
    echo -e "Platform: ${YELLOW}Multi-architecture (amd64, arm64)${NC}"
    
    # Check if buildx is available
    if ! docker buildx version > /dev/null 2>&1; then
        echo -e "${RED}Error: Docker buildx is not available. Please enable it in Docker Desktop settings.${NC}"
        exit 1
    fi
    
    # Create buildx builder if it doesn't exist
    if ! docker buildx inspect mybuilder > /dev/null 2>&1; then
        echo "Creating buildx builder..."
        docker buildx create --name mybuilder --use
    else
        docker buildx use mybuilder
    fi
    
    # Build and push multi-architecture image
    echo -e "${YELLOW}Building multi-architecture image...${NC}"
    echo -e "${RED}Note: Multi-architecture builds require pushing to a registry.${NC}"
    echo -e "${YELLOW}You'll need to be logged in to a Docker registry.${NC}"
    
    read -p "Do you want to continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker buildx build --platform linux/amd64,linux/arm64 -t ${IMAGE_NAME}:${TAG} --push .
    else
        echo "Multi-architecture build cancelled."
        exit 0
    fi
else
    echo -e "Platform: ${YELLOW}${PLATFORM}${NC}"
    
    # Build for specific platform
    if [ "$PLATFORM" = "amd64" ]; then
        echo -e "${YELLOW}Building for AMD64 (x86_64)...${NC}"
        docker build -t ${IMAGE_NAME}:${TAG} .
    else
        echo -e "${YELLOW}Building for ARM64...${NC}"
        docker build --platform=linux/arm64 -t ${IMAGE_NAME}:${TAG} .
    fi
fi

# Check build result
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Build successful!${NC}"
    echo -e "Image: ${YELLOW}${IMAGE_NAME}:${TAG}${NC}"
    
    # Show run example
    echo -e "\n${GREEN}To run the container:${NC}"
    echo -e "${YELLOW}docker run -d --name bastion-gateway --network=host --restart unless-stopped ${IMAGE_NAME}:${TAG}${NC}"
else
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi 