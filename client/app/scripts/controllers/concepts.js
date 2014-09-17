'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:ConceptsCtrl
 * @description
 * # ConceptsCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('ConceptsCtrl', function ($scope) {
    $scope.awesomeThings = [
      'HTML5 Boilerplate',
      'AngularJS',
      'Karma'
    ];
  });
