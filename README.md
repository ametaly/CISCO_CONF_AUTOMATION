
# README - Projet 3TCA NAS

## Contributeurs

Amet Aly Toure (amet.toure@insa-lyon.fr)
Mikaîl Ounissi (mikail.ounissi@insa-lyon.fr )
Nathan Lehodey (nathan.lehodey@insa-lyon.fr)
Nicolas Leportier (nicolas.lepotier@insa-lyon.fr)
Mahamat Tahir Saleh (tahir.mahamat-saleh@insa-lyon.fr)
Alaaeddine Ahriz (alaaeddine.ahriz@insa-lyon.fr)


## Objectif

L'objectif de ce projet est d'automatiser le provisionnement des services VPN BGP/MPLS sur un réseau utilisant le logiciel GNS3. Plus précisément, nous cherchons à ajouter des fonctionnalités MPLS et BGP/MPLS VPN à un projet GNS existant.
Pour cela, on définit un fichier .json d'intention, où on décrit la topologie de notre réseau avec les services au niveau de chaque interface.
Ensuite un code python lit ce fichier intention et produit en conséquence un fichier de configuration pour chaque routeur. Et finalement, un autre code python lit ces fichiers de configuration pour lancer, avec l'aide de telnet, les configurations au niveau des routeurs sur GNS3.

## Architecture du réseau

![alt text](image.png)

## Guide de démarrage rapide
### Configuration GN3
En faisant un pull du projet, vous aurez en local entre autres le fichier GNS3 **fin.gns3** et le répertoire qui contient les configs
des routeurs **project-files**.

Il suffit juste (en ayant GNS3 bien configuré sur votre machine en local avec la bonne image de routeur), de lancer le fichier **fin.gnS3**.d

### Génération de Configuration avec python depuis le fichier d'intention

Utiliser le script Python **generate_config_files.py** pour générer les fichiers de configuration pour chaque routeur.
Les fichiers de configuration seront sauvegardés dans le répertoire dev/config_files.

### Déploiement des Configurations avec telnet

Utiliser le script Python **telnet_deployment.py** pour déployer les configurations sur chaque routeur.
Ce script se connectera à chaque routeur via Telnet et enverra les commandes de configuration.
Le script nécessite les port sur lesquels sont connectés les routeurs en local: 
    - il faut donc consulter les numéros de port des routeur au niveau de l'UI de GNS3 (à gauche souvent): penser à bien démarrer tous les routeurs!
    - ensuite dans le code source **deploy_telnet.py**, faut renseigner les ports pour les routeurs correspondant dans le dictionnaire **routers_gns3**: par exemple routers_gns3 = {
                                                        "PE1": "5002",
                                                        "PE2": "5006",
                                                        "P1": "5014",
                                                        ...
                                                        }

## Notes Supplémentaires

- L'automatisation de la configuration et du déploiement est cruciale pour ce projet. Les scripts Python fournis facilitent grandement ce processus.
- Assurez-vous de suivre les phases du projet dans l'ordre indiqué pour une progression logique et méthodique.
- Pour des détails spécifiques sur la configuration des routeurs et des protocoles, référez-vous aux ressources Cisco IOS et aux documents de référence mentionnés dans le projet.
