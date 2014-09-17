'use strict';

describe('Controller: StatsCtrl', function () {

  // load the controller's module
  beforeEach(module('svenClientApp'));

  var StatsCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function ($controller, $rootScope) {
    scope = $rootScope.$new();
    StatsCtrl = $controller('StatsCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function () {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
