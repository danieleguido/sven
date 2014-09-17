'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:AboutCtrl
 * @description
 * # AboutCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('AboutCtrl', function ($scope) {
    $scope.awesomeThings = [
      'HTML5 Boilerplate',
      'AngularJS',
      'Karma'
    ];
  });
