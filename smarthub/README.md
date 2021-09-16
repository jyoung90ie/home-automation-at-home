# Smart Hub

## Deployment

This was developed to be deployed on any device that supports docker and as such the steps below assume you already have `Docker` and `docker-compose` installed.
### Raspbian

This was deployed 



# Smart Hub

I created this for my MSc Software Development at [Queen's University Belfast](https://www.qub.ac.uk/courses/postgraduate-taught/software-development-msc/) dissertation to demonstrate my learning and understanding throughout the course. 

I chose to develop a smart home automation system which handles the end-to-end communication, from the source devices to the devices/notificaionts that should be triggered when user-defined triggers have been met. This was a complex project which allowed me to advance my understanding of communication protocols (such as [MQTT](https://mqtt.org/)) and the importance of optimising code throughout (e.g. to avoid unneccessary database queries).

## Deployed Application

TBC

## Demonstration Data & Accounts

To enable you to test the website functionality, a number of demo accounts, products, and, transactions have been created. You can access this data using the accounts below. 

| Email | Password | Desription |
| ----- | -------- | ---------- |
| TBC | TBC | TBC  |
| TBC | TBC | TBC|

## UX

Given the application has been designed to help the end-user manage smart home devices and develop custom automations, the UX is designed to be clean and intuitive. Navigation is consistent, colours, buttons, and positioning will all be familiar once the user has sampled each one. Given the complexity of the backend code, it was important for me to present a simple and intuitive user experience - which is what has been developed.

### User Stories

#### Smart Home User

As a customer I want to be able to...

- TBC
- TBC


## Features

### Existing Features

This package enables you to build and deploy a functional smart home hub for managing your smart devices. At present, the platform supports only Zigbee devices, but future developments will expand this capability to incorporate other protocols, such as API based devices.

The package has been broken into individual apps, the features of which are detailed under each of the headings below.

#### Custom User Model

To capture additional user information, such as home location, I opted to override the default Django user model and create a custom one. This enabled me to store all the necessary user data in one object. It will also make any future user model changes easier to make.

Given the additional data input requirements, I had to specify custom forms in order to capture all the required information. This included overriding Django default forms, for example, the admin forms for adding/modifying user details.

#### Users

This is where all customer information is retained via the custom user model. I also made the decision to use Django-allauth which added the ability to override the username field, using the email address as the login. It also brought with it the ability to verify email addresses and reset passwords.

Within this app I have overriden a number of the default forms provided by `django-allauth` to integrate with the custom user model. To produce responsive forms I have used the django-crispy-forms helper function which eanbled me to create custom form layouts with individual element styling. I have also modified the rendering of the django admin site for the user object, to provide a better structure.

Outlined below are the views that are produced by this app:

a) **Signup:** a custom form used to create a new user account with the custom user model. The username field is removed, with the email address used in it's placed. Given this is a smart hub platform, it made sense to capture the user's home location, so that future developments could use this as a trigger for automation.

b) **Login:** Enables users to login using their email address and password. 

c) **Logout:** Enables users to logout of their account. The user will be asked to confirm they wish to logout of their account, this prevents accidental logout. When a user logs out they will be unable to access any device/automation functionality - this is to prevent unauthorised users from change device data.

d) **Social login - Gmail:** Users can login using an existing Gmail account - this has been setup using Google's OAuth2 service and enables a user to hit the 'ground running' - with additional information captured under the user profile. To support this I created a custom `adapter` which overrode the default `django-allauth` implementation, using fields specific to this platform.

e) **Profile:** Here the user can update their personal details, including changing their home location.

f) **Profile - Change email:** A user can have multiple emails if they wish, this functionality is leveraged from `django-allauth`. The user can log in with all email addresses under their account. 

g) **Profile - Change password:** For security, a user must provide their current password alongside a new password before it will be accepted and updated.

#### MQTT

As I was developing an end-to-end solution, I needed a way for _sniff_ communications from the zigbee devices. I opted not use to a Zigbee router as this would require investment in a brand and likely would come with limitations placed by the manufacturer. Instead, I opted to purchase this [Zigbee sniffer](https://www.amazon.co.uk/dp/B07YDG4QHM/ref=cm_sw_r_cp_apa_glt_fabc_KVCAQ6ETZ1WWWKGCQJY0?_encoding=UTF8&psc=1&pldnSite=1).

To setup the hardware device, it needs to be flashed with custom firmware that publishes to an MQTT broker - see [instructions here](https://www.zigbee2mqtt.io/information/alternative_flashing_methods.html).

For this to work, you must have an MQTT broker installed - in this case I opted to use [Mosquitto](https://mosquitto.org/) with default settings.

With all of the above in place, we can now move on to how the Smart Hub platform communicates with devices. There are a number of components that make up this app, which I have outlined below:

a) **Listener:** 

b) **Publisher:** 

c) **Management Command:** 

d) **Toggle View:** 

e) **Trigger View:** 

f) **Customised Admin Functionality:** 

g) **Create Order:** 

#### Devices

TBC

a) **TBC:** 

b) **TBC:** 

c) **TBC:** 

d) **TBC:** 

#### Events

TBC

a) **TBC:** 

b) **TBC:** 

c) **TBC:** 

d) **TBC:** 

#### Pages

The Pages app is used to website pages which are not related to any specific app. In this instance, the homepage and about us page are delivered via this app. It sets up the urls and delivers the templates to the end user.

#### Notifications

TBC

a) **TBC:** 

b) **TBC:** 

c) **TBC:** 

d) **TBC:** 

#### Settings

Normally Django settings are contained within a single file, settings.py, within the project folder. However, in the interest of security and trackability, I have created a settings folder. This contains a number of files which are detailed below:

a) **base.py:** this contains the 'base' settings which are common across all environments that this application has been deployed on. This does not contain any sensitive information. Some of the specific deployment files, listed after this, may override some of these settings if necessary.

b) **local.py:** this contains all settings specific to my local development environment, for example, permissible addresses, database accesses, etc.

c) **test.py:** this contains the settings required to deploy to my test environment, in this case, these are the settings I use to run my application on Travis CI.

d) **production.py:** these are the settings used for deployment in the production environment.

### Features to be implemented

- TBC
- TBC

## Challenges

- TBC

- TBC

## Technologies Used

- [HTML](https://www.w3schools.com/html/default.asp)
  - This is the most fundamental component of a web page, providing the structure and content which can then be then be styled by CSS and interacted with by JavaScript.

- [CSS](https://www.w3schools.com/css/default.asp)
  - This is a styling language which is used to modify how the HTML is render to the user, for example, the fonts used, colours, sizes, etc.
  - To override default Bootstrap styling and provide my own custom styling I have created my own CSS file, base.css, which is applied to every page.

- [JavaScript](https://www.w3schools.com/Js/)
  - This language enables an interactive element to be added to websites, permitting realtime responsive pages.

  - To use Bootstrap tabs with the template I had to write custom JS code to override the default Bootstrap.js function and replace it with code that worked for me.
  - The navigation menu becomes fixed once the user scrolls past the header and brand container, this is achieved using custom JS code and Bootstrap classes.

- [Python](https://www.python.org/)
  - This is the server side language the application has been developed using.

- [PostgreSQL](https://www.postgresql.org/)
  - This is an open source database which I have developed the application on.
  - I have created a docker container which runs PostgreSQL and interacts with the Python application.

- [Docker](https://www.docker.com/)
  - This is a technology which packages up applications into containers and runs them in an isolated container within a chosen operating system, which is seperate from the host operating system.
  - TBC - confirm why I used Docker

### Frameworks

- [Bootstrap](https://getbootstrap.com/)
  - This is a front-end framework which is built using HTML and CSS. It makes it easy to create responsive websites using a grid system with screen-width breakpoints.

- [JQuery](https://jqueryui.com/)
  - This is a JavaScript framework which enables easy manipulation of the Document Object Model (DOM) using JQuery syntax.
  - This was used to provide the interactive functionality for fetching device's and device command's for setting up event triggers and responses.

- [Font Awesome](https://fontawesome.com/)
  - This is a font library which I have used to provide some context appropriate icons throughout the application. For example, the Basket icon.

- [Django](https://www.djangoproject.com/)
  - This is a high-level python framework which provides advanced functionality with minimal effort from the developer.
  - The application is developed using Django and extensively uses built-in functionality and custom packages.

- [Django-allauth](https://www.intenct.nl/projects/django-allauth/)
  - This package is an add-on app for Django which implements a third-party authentication system. It provides advanced functionality, such as the integration of external social authentication, e.g. allowing users to authenticate with your website using their Google account, in addition to local authentication.
  - For this application I have used this package for its additional security, as it will only permit a user to attempt to login with incorrect details 5 times before restricting their ability to do so. This is important given it is an ecommerce application. It also enabled me to develop the application using email address as the user login and remove the unneccessary username field in the custom user model.

- [Django-crispy-forms](https://github.com/django-crispy-forms/django-crispy-forms)
  - This package renders Django forms using Bootstrap conventions and classes, effectively making the forms responsive and mobile-first.
  - It also permits customisation of form rendering, from layout, to individual field styles.
  - I have used this package throughout to provide better structured forms with responsive design.

## Testing

### Automated

TBC - point to the report 

### Manual

In addition to the automated testing, I conducted some manual testing across a number of browsers and devices. This was to ensure, the pages rendered as expected, and that screen space was optimally utilised.

| # | Test | Test Criteria | Result |
|---|------|--------|------|
| 1 | Website is displayed correctly on multiple browsers | Tested on Chrome, Safari, and Edge | Passed |
| 2 | Website is responsive and displayed correctly on multiple devices | Tested on Macbook Pro, Windows Laptop, OnePlus 7T, and iPhone | Passed |
| 3 | Forms do not permit entry of invalid data; invalid entries receive an error message | Attempting to update basket quantity to more than the maximum permitted amount (i.e. > 5) | Passed |
| 4 | All links work | Check that all links are work | Passed |
| 5 | Images, icons, and buttons render correctly | Visual inspection of every page | Passed |

### Known bugs

TBC

## Deployment

### ENV file

| KEY  | VALUE |
| ---- | ----- |
| `TBC` | `TBC` |
| `TBC` | `TBC` |
| `TBC` | `TBC` |
| `TBC` | `TBC` |
| `TBC` | `TBC` |
| `TBC` | `TBC` |
| `TBC` | `TBC` |
| `TBC` | `TBC` |

### Pushbullet setup (for notifications)

TBC

### Raspberry Pi with Raspbian 

TBC

### Local machine deployment

TBC

## Credits

TBC

### Acknowledgements

- Dissertation Supervisor - Neil Anderson - for feedback and guidance at various points throughout the project.