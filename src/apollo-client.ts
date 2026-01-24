import { ApolloClient, InMemoryCache, HttpLink, DefaultOptions } from '@apollo/client/core';
import { setContext } from '@apollo/client/link/context';
import Cookies from 'js-cookie';

// Optional: Define default options type if you customize (e.g., for fetchPolicy)
const defaultOptions: DefaultOptions = {
  watchQuery: {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'ignore',
  },
  query: {
    fetchPolicy: 'network-only',
    errorPolicy: 'all',
  },
};

const graphqlEndpoint: string | undefined = import.meta.env.VITE_GRAPHQL_ENDPOINT;

if (!graphqlEndpoint) {
  throw new Error('GraphQL endpoint is not defined in environment variables.');
}

const httpLink = new HttpLink({
  uri: graphqlEndpoint,
  credentials: 'include',
  // headers: { 'X-CSRFToken': Cookies.get('csrftoken') || '' },
});

const getDjangoCsrfToken = () => Cookies.get('csrftoken') || '';


const authLink = setContext((_, { headers }) => {
  const csrfToken = getDjangoCsrfToken();
  const token = localStorage.getItem('authToken');
  return {
    headers: {
      ...headers,
      Authorization: token ? `Bearer ${token}` : '',
      'X-CSRFToken': csrfToken, 
 
    },
  };
});

const cache = new InMemoryCache();

const apolloClient = new ApolloClient({
  link: authLink.concat(httpLink),
  cache,
  defaultOptions, // for better type inference in queries
});

export default apolloClient;