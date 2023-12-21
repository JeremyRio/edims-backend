# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of your application's code
COPY . .

# Build the TypeScript app
RUN npm run build

# Your app binds to port 8080 so use the EXPOSE instruction to have it mapped
EXPOSE 8080

# Define the command to run your app
CMD [ "node", "dist/index.js" ]
