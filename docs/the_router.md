## The router
The router is the component responsible for:

* identyfing the type of the request
* route to the right component

### Handling Different Types of Requests

We can handle different types of requests.

#### Example 1

**Request:**

> *"Show me all the sales made in Q3 2024."*

If the data is available, this request can be translated into an SQL statement to query the database.

#### Example 2

**Follow-up Request:**

> *"Create a report titled 'Sales by Product Q3 2024'. Group the data by product and display it in a tabular format."*

This type of request involves generating a report and can be fulfilled by the LLM using the data retrieved from the database.

#### Routing Requests

As we can see, not all requests are the same. We need a way to determine the nature of each request and route it to the appropriate component accordingly.

In the overall architecture of the solution, **this is the role of the Router**.


## AI in the Router
