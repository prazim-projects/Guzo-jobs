<script lang="ts" setup>
import { useQuery } from '@vue/apollo-composable';
import gql from 'graphql-tag';


const usersQuery = gql`
  query allUsersQuery {
    users {
        email
        id
        phoneNumber
        trustScore
        username
  }
}
`;

const { result, loading, error } = useQuery(usersQuery);

</script>


<template>
    <div>
    <h1>User List</h1>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">Error: {{ error.message }}</div>
    <ul v-else>
      <li v-for="user in result.users" :key="user.id">
        <strong>{{ user.username }}</strong> - {{ user.email }} - {{ user.phoneNumber }} - Trust Score: {{ user.trustScore }}
      </li>
    </ul>
    </div>

</template>

<style lang="css" scoped>


</style>