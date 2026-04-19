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

const devFallbackEndpoint = localStorage.getItem('graphqlEndpoint') || 'http://10.0.2.2:8000/graphql';
const graphqlEndpoint = import.meta.env.VITE_GRAPHQL_ENDPOINT || (import.meta.env.DEV ? devFallbackEndpoint : '');

if (!graphqlEndpoint) {
  throw new Error('Set VITE_GRAPHQL_ENDPOINT for production builds.');
}

const httpLink = new HttpLink({
  uri: graphqlEndpoint,
  credentials: 'omit',
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