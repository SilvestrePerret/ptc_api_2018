"""
This is the magic !

In this module, we generate the specific required tasks for each trip !
"""
from datetime import timedelta
from ptc_api_back.models import Country, Climate


class TaskFactory:
    """
    Factory class designed to help create various tasks.
    """

    def __init__(self, **kwargs):
        self.trip = kwargs['trip'] if 'trip' in kwargs else None
        self.tasks = []
        self.a_country = None
        self.d_country = None

    def create_tasks(self):
        """
        Call the task_factory method to create the differents tasks.
        """
        try:
            self.a_country = Country.objects.get(
                name=self.trip.arrival_country)
        except Country.DoesNotExist:
            pass

        try:
            self.d_country = Country.objects.get(
                name=self.trip.departure_country)
        except Country.DoesNotExist:
            pass

        self.create_passport_task()

        self.create_visa_task()

        if bool(self.a_country):
            self.create_vaccines_task()
            self.create_malaria_task()

        self.create_weather_task()
        self.create_flight_needs_task()
        self.create_banking_task()

        if bool(self.a_country):
            self.create_insurance_task()

        self.create_systematic_tasks()  # 3 tasks

        if self.trip.return_date_time is None or\
            self.trip.return_date_time - self.trip.arrival_date_time > timedelta(days=14):

            self.create_long_travel_task()

        for task in self.tasks:
            task.auto = True

        return self.tasks

    def create_passport_task(self):
        """
        Voir Donnée non formatée de l'année dernière IATA github !
        """
        self.tasks.append(self.trip.tasks.create(
            title="Check Passport Validity Date",
            comments="Most of the time, your passport has to be valid " +\
            "at least for the three months following your departure."
        ))

    def create_visa_task(self):
        if not bool(self.d_country) or not bool(self.a_country):
            self.tasks.append(self.trip.tasks.create(
                title="Visa may be needed.",
                comments="We don't have your country in our base, " +\
                "retry with its name in English please."
            ))
            return

        d_country = self.d_country
        a_country = self.a_country

        common_unions = set()
        for union in d_country.countryunion_set.all():
            if bool(union.countries.filter(id=a_country.id)):
                common_unions.add(union)

        if bool(common_unions):
            for union in common_unions:
                if not union.t_visa_between_members:
                    self.tasks.append(self.trip.tasks.create(title="No Visa Needed"))

        for union in a_country.countryunion_set.all():
            if union.common_visa:
                self.tasks.append(self.trip.tasks.create(
                    title=union.name + "Visa or"
                ))

        self.tasks.append(self.trip.tasks.create(
            title=a_country.name + "'s Visa Needed",
            comments="Contact the Ambassy of your destination country."
        ))

    def create_vaccines_task(self):
        """
        Call the API of TuGo
        https://api.tugo.com/v1/travelsafe/countries/[CodeCountry]
        headers must contain : "X-Auth-API-Key":"jttuskf9wetdbzspvtt6kagb"
        """
        comments = ""
        vaccines = self.a_country.vaccines.all()
        if bool(vaccines):
            content = ""
            for vaccine in vaccines:
                content += f"{vaccine.category}\n"
            self.tasks.append(self.trip.tasks.create(
                title="Check your vaccines (+)",
                comments=comments,
                deadline=self.trip.departure_date_time - timedelta(days=45)
            ))

        self.tasks.append(self.trip.tasks.create(
            title="Check vaccines for " + self.trip.arrival_country,
            comments="Both required and advised vaccines !",
            deadline=self.trip.departure_date_time - timedelta(days=45)
        ))

    def create_malaria_task(self):
        """
        Check if country has malaria presence.
        """
        if self.a_country.malaria_presence:
            self.tasks.append(self.trip.tasks.create(
                title="Protection for mosquito bites",
                comments="insect repellent, insecticide-treated bednet, pre-treating clothing, ..."
            ))

    def create_weather_task(self):
        """
        Climate information comes from Tugo.
        They may be frightening ;-)
        """
        try:
            climate = Climate.objects.get(country=self.a_country)
            self.tasks.append(self.trip.tasks.create(
                title=f"Check climate in {self.a_country.name} (+)",
                comments=climate.description
            ))
        except (Climate.DoesNotExist, Country.DoesNotExist):
            self.tasks.append(self.trip.tasks.create(
                title="Check meteo",
                comments="Check weather conditions in " +
                self.trip.arrival_country + " and prepare appropriate clothing"
            ))

    def create_flight_needs_task(self):
        """
        Create a task "take some food/drinks/books/earplugs" if the flight is too long.
        """
        duration = self.trip.arrival_date_time - self.trip.departure_date_time
        if duration > timedelta(hours=2):
            self.tasks.append(self.trip.tasks.create(
                title="Flight Must Have !",
                comments="Take your earplugs and your sleep mask for your flight"
            ))
        else:
            self.tasks.append(self.trip.tasks.create(
                title="Flight Must Have !",
                comments="Take some food and some drinks for your flight"
            ))

    def create_banking_task(self):
        self.tasks.append(self.trip.tasks.create(
            title="Check your banking fees",
            comments="You should contact your bank account manager " +\
            "to ask the amount of banking fees you will have to pay " +\
            "when you will pay with your card or when you will use a cash machine."
        ))

    def create_insurance_task(self):
        level = self.a_country.advisory_state
        if not level is None:
            self.tasks.append(self.trip.tasks.create(
                title="Check rapatriation insurance",
                comments="It seems to be recommended for this country !" if level > 0\
                    else "Not really required but if you need this to relax yourself, go on :-)"
            ))
        else:
            self.tasks.append(self.trip.tasks.create(
                title="Check required insurance",
                comments="We got no information for your country, sorry !"
            ))

    def create_systematic_tasks(self):
        self.tasks.append(self.trip.tasks.create(
            title="Check cabin baggage dimensions",
            comments="Ask your company website which size your cabin baggage can be."
        ))
        self.tasks.append(self.trip.tasks.create(
            title="Labels on your baggages",
            comments="It really helps if your baggages are lost during the flight !"
        ))
        self.tasks.append(self.trip.tasks.create(
            title="Make copies of your pappers.",
            comments="Put one copy of your passport, " +\
            "your visa and your flight ticket in each luggage. " +\
            "Copy them on your smartphone and have them on the internet."
        ))

    def create_long_travel_task(self):
        """
        TODO
        """
        self.tasks.append(self.trip.tasks.create(
            title="Long travel To-Do",
            comments=""
        ))