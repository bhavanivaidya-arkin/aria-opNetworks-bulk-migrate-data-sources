## Bulk Migration of Data Sources to a New Collector VM

The task of migrating data sources from one collector VM to another has transformed into a streamlined and efficient process using this script. This seamless migration endeavor ensures minimal disruption to data flow while maximizing precision and reliability.

The orchestrated migration process follows a meticulously crafted strategy. Initial steps involve thorough analysis of the existing data sources and their dependencies, ensuring a comprehensive understanding of the ecosystem. Subsequently, the data sources are migrated to another collector VM.

During the migration, data integrity remains paramount. Robust validation mechanisms are employed to guarantee that data remains consistent and uncorrupted during transit. Automation plays a pivotal role in this migration . Cutting-edge tools orchestrate the transfer, alleviating manual intervention and mitigating the risk of human error. Real-time monitoring provides insights into the migration's progress, affording opportunities for proactive adjustments and optimizations.

The result is a harmonious transition – data sources flowing seamlessly from the old collector VM to the new one. Operational downtime is minimized, ensuring uninterrupted access to critical information. 
#### Instructions are provided while running the script

## Script requirements 

Ensure python is installed from where the script is ran and also there are the required util files listed below 
* requests 
* urllib3
* configparser
* csv
* os
* json
* from itertools import zip_longest

## Configuration file
#### api_config.ini

This file contains the configuration details of the instance from where the migration of the data sources should occur.
Details to be configured -

* ip_address
* port
* username
* password

This file also contains the apis that are triggered to ensure that migration occurs

## Usage

python3 auth_data_sources_all.py

## Example

## Contact

@bhavanivaidya-arkin started this project. Reach out to me via Issues Page here on GitHub. If you want to contribute, also get in touch with me.
