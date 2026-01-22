import { ApolloClient, InMemoryCache, HttpLink, DefaultOptions } from '@apollo/client/core';
import { setContext } from '@apollo/client/link/context';

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
  // headers: { Authorization: `Bearer ${import.meta.env.VITE_API_KEY as string}` }
});

// const authLink = setContext()

const cache = new InMemoryCache();

const apolloClient = new ApolloClient({
  link: httpLink,
  cache,
  defaultOptions, // for better type inference in queries
});

export default apolloClient;