# Use the .NET 6.0 SDK version for the build stage
FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build

# Set the working directory in the container
WORKDIR /src

# Copy the entire solution directory (including all projects)
COPY . .

# Restore dependencies for all projects
RUN dotnet restore OMF.API/OMF.API.csproj

# Build the application
RUN dotnet build OMF.API/OMF.API.csproj -c Release -o /app/build

# Publish the application
RUN dotnet publish OMF.API/OMF.API.csproj -c Release -o /app/publish

# Use the .NET 6.0 runtime as a base image
FROM mcr.microsoft.com/dotnet/aspnet:6.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish .

# Set the environment variable to change the listening port to 9048
ENV ASPNETCORE_URLS=http://+:9048

# Set the entry point for the container
ENTRYPOINT ["dotnet", "OMF.API.dll"]

# Expose the default port (80) and 9048
EXPOSE 80
EXPOSE 9048
