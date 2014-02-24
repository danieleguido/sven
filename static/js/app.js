'use strict';


// Declare app level module which depends on filters, and services
angular.module('sven', [
  'ngRoute',
  'sven.filters',
  'sven.services',
  'sven.directives',
  'sven.controllers'
]).
config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/corpus', {templateUrl: '/static/partials/corpus.list.html', controller: 'MyCtrl1'});
  $routeProvider.when('/document', {templateUrl: '/static/partials/document.list.html', controller: 'MyCtrl2'});
  $routeProvider.otherwise({redirectTo: '/corpus'});
}]);