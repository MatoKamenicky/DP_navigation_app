# Navigation App with PostgreSQL and Python

## Overview

This repository contains the source code for a navigation application developed as part of a diploma thesis. The application focuses on providing efficient route planning, taking into account obstacles such as bridges and underpasses that are relevant only for heavy or large-size vehicles.

## Features

- **Shortest Path Calculation**: Utilizes PostgreSQL and PostGIS for efficient storage and retrieval of geospatial data to compute the shortest path.
- **Obstacle Handling**: Incorporates obstacle-aware navigation, where obstacles like bridges and underpasses impact routing only for specific vehicle types.
- **OpenStreetMap (OSM) Integration**: Utilizes OpenStreetMap data for enriched geospatial information.
- **City Hall Data**: Integrates data from the Bratislava City Hall for enhanced accuracy in local navigation.

## Requirements

- Python
- Django
- PostgreSQL
- PostGIS

## Getting Started

To run the navigation app locally, follow these steps:

1. **Clone the Repository**: 
   ```bash
   git clone https://github.com/MatoKamenicky/DP_navigation_app.git

2. **Navigate to the navigation_web_app**: 

3. **Start the Django Development Server:**: 
   ```bash
   python manage.py runserver

